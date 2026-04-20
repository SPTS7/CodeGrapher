import asyncio
import json
import logging
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from codegrapher.parsers import get_parser, is_supported_file
from codegrapher.models import FunctionInfo, CodeAnalysisError

# --- Dependency Handling ---
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

try:
    from gitignore_parser import parse_gitignore
    GITIGNORE_AVAILABLE = True
except ImportError:
    parse_gitignore = None
    GITIGNORE_AVAILABLE = False

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CACHE_DIR = ".codegraph_cache"
CACHE_FILE = os.path.join(CACHE_DIR, "cache.json")

def load_cache() -> Dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"ast_cache": {}, "ai_cache": {}}
    return {"ast_cache": {}, "ai_cache": {}}

def save_cache(cache_data: Dict):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save cache: {e}")

# --- Core Analysis Components ---
def _get_supported_files(root: Path) -> List[Path]:
    gitignore_path = root / '.gitignore'
    matches = None
    if gitignore_path.is_file() and GITIGNORE_AVAILABLE:
        try:
            matches = parse_gitignore(gitignore_path, root)
        except Exception as e:
            logger.warning(f"Failed to parse .gitignore: {e}")

    all_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune hidden dirs and common excludes in-place
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ('node_modules', '__pycache__')]
        
        # Prune ignored directories if .gitignore is present
        if matches:
            dirnames[:] = [d for d in dirnames if not matches(Path(dirpath) / d)]
            
        for f in filenames:
            p = Path(dirpath) / f
            if is_supported_file(p):
                if matches and matches(p):
                    continue
                all_files.append(p)
                
    return all_files

def analyze_project(project_path_str: str) -> Tuple[Dict[str, Dict], List[str]]:
    project_path = Path(project_path_str)
    logs = [f"Searching for supported code files in {project_path}..."]
    source_files = _get_supported_files(project_path)
    logs.append(f"Found {len(source_files)} files to analyze.")
    
    cache = load_cache()
    if "ast_cache" not in cache: cache["ast_cache"] = {}
    
    all_functions = {}
    cache_updated = False
    
    for src_file in source_files:
        try:
            with open(src_file, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
                
            file_hash = hashlib.md5(code.encode('utf-8')).hexdigest()
            file_path_str = str(src_file.resolve())
            
            # Check cache
            if file_path_str in cache["ast_cache"] and cache["ast_cache"][file_path_str].get("hash") == file_hash:
                all_functions.update(cache["ast_cache"][file_path_str]["functions"])
                continue
                
            ParserClass = get_parser(src_file)
            if not ParserClass: continue
            
            parser = ParserClass(source_code=code, file_path=src_file)
            funcs_dict = parser.parse()
            
            all_functions.update(funcs_dict)
            
            # Update cache
            cache["ast_cache"][file_path_str] = {
                "hash": file_hash,
                "functions": funcs_dict
            }
            cache_updated = True
            
        except Exception as e:
            logs.append(f"[Warning] Could not process {src_file}: {e}")

    if cache_updated:
        save_cache(cache)

    return all_functions, logs

def build_call_graph(all_functions: Dict, entry_points: List[str], max_depth: int = 10) -> Dict:
    graph = {}
    queue = [(name, 0) for name in entry_points if name in all_functions]
    processed = set()
    while queue:
        func_name, depth = queue.pop(0)
        if func_name in processed or depth > max_depth: continue
        processed.add(func_name)
        if func_name in all_functions:
            graph[func_name] = all_functions[func_name]
            for called_func in all_functions[func_name]['calls']:
                if called_func not in processed: queue.append((called_func, depth + 1))
    return graph

# --- AI and Visualization Components ---
class AIDocumenter:
    def __init__(self, api_key: str):
        if not GENAI_AVAILABLE: raise CodeAnalysisError("Google GenAI library not installed.")
        self.client = genai.Client(api_key=api_key)
        self.semaphore = asyncio.Semaphore(5) # Rate limit to 5 concurrent requests
        self.cache = load_cache()
        if "ai_cache" not in self.cache: self.cache["ai_cache"] = {}

    async def _generate_summary(self, func_info: Dict, target: str) -> str:
        source_code = func_info['source_code']
        code_hash = hashlib.md5(f"{target}_{source_code}".encode('utf-8')).hexdigest()
        
        # Check AI Cache
        if code_hash in self.cache["ai_cache"]:
            return self.cache["ai_cache"][code_hash]

        if target == "ai":
            prompt = f"Analyze this Python function and provide a dense, technical summary of its behavior, inputs, outputs, and side-effects. Optimize for another AI to read.\n\n```python\n{source_code}\n```"
        else:
            prompt = f"Analyze this Python function and provide a concise, one-sentence summary of its purpose, starting with a verb.\n\n```python\n{source_code}\n```"
            
        try:
            async with self.semaphore:
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                summary = response.text.strip().replace('*', '') or "Failed to generate summary."
                self.cache["ai_cache"][code_hash] = summary
                return summary
        except Exception as e:
            return f"AI summary failed: {e}"

    async def enrich_graph(self, call_graph: Dict, target: str) -> List[str]:
        logs = ["--- 🧠 Starting AI Documentation ---"]
        tasks = {name: self._generate_summary(info, target) for name, info in call_graph.items()}
        summaries = await asyncio.gather(*tasks.values())
        
        for (name, info), summary in zip(call_graph.items(), summaries):
            info['summary'] = summary
            logs.append(f"  - Generated docs for '{name}'")
            
        save_cache(self.cache)
        return logs

async def enrich_with_ai_summaries_async(call_graph: Dict, api_key: str, target: str = "human") -> List[str]:
    if not api_key: return ["Skipping AI enrichment: No API key provided."]
    try:
        return await AIDocumenter(api_key).enrich_graph(call_graph, target)
    except Exception as e: return [f"AI enrichment failed: {e}"]

def generate_interactive_diagram_data(call_graph: Dict) -> Dict[str, Any]:
    nodes, edges = [], []
    
    # *** FIX IS HERE ***
    # Calculate complexity scores safely
    complexity_scores = [info.get('complexity', 0) for info in call_graph.values()]
    # Ensure max_complexity is at least 1 to prevent division by zero
    max_complexity = max(1, max(complexity_scores) if complexity_scores else 1)

    for func_name, func_info in call_graph.items():
        complexity = func_info.get('complexity', 0)
        # Scale node size based on complexity
        size = max(20, min(50, (complexity / max_complexity) * 30 + 20))

        nodes.append({
            'id': func_name, 
            'label': func_name, 
            'title': func_info.get('summary', ''),
            'source_code': func_info['source_code'],
            'size': size,
            'shape': 'diamond' if func_info.get('is_async') else 'box'
        })
        for called_func in func_info['calls']:
            if called_func in call_graph: 
                edges.append({'from': func_name, 'to': called_func})
    return {'nodes': nodes, 'edges': edges}
