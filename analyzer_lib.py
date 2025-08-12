import ast
import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# --- Dependency Handling ---
try:
    import google.generativeai as genai
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

# --- Custom Exception & Data Structures ---
class CodeAnalysisError(Exception):
    pass

@dataclass
class FunctionInfo:
    name: str
    calls: List[str]
    source_code: str
    file_path: str
    complexity: int = 0
    summary: str = "No AI summary generated."
    line_number: int = 0
    is_async: bool = False
    is_method: bool = False
    docstring: Optional[str] = None

# --- Core Analysis Components ---
class FunctionCallVisitor(ast.NodeVisitor):
    def __init__(self, source_code: str, file_path: Path):
        self.functions: Dict[str, FunctionInfo] = {}
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None
        self.source_code_str = source_code
        self.file_path_obj = file_path

    def _get_qualified_name(self, name: str) -> str:
        return f"{self.current_class}.{name}" if self.current_class else name

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculates the cyclomatic complexity of a function node."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.And, ast.Or)):
                complexity += 1
        return complexity

    def visit_ClassDef(self, node: ast.ClassDef):
        outer_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = outer_class

    def _process_function_node(self, node: ast.AST):
        func_name = self._get_qualified_name(node.name)
        outer_function = self.current_function
        self.current_function = func_name
        self.functions[func_name] = FunctionInfo(
            name=func_name, calls=[],
            source_code=ast.get_source_segment(self.source_code_str, node) or "# Source not available",
            file_path=str(self.file_path_obj.resolve()),
            line_number=node.lineno,
            complexity=self._calculate_complexity(node),
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=self.current_class is not None,
            docstring=ast.get_docstring(node)
        )
        self.generic_visit(node)
        self.current_function = outer_function

    def visit_FunctionDef(self, node: ast.FunctionDef): self._process_function_node(node)
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef): self._process_function_node(node)

    def visit_Call(self, node: ast.Call):
        if self.current_function and self.current_function in self.functions:
            try:
                call_name = ast.unparse(node.func)
                if '.' in call_name: call_name = call_name.split('.')[-1]
                if call_name not in self.functions[self.current_function].calls:
                    self.functions[self.current_function].calls.append(call_name)
            except Exception: pass
        self.generic_visit(node)

def _get_python_files(root: Path) -> List[Path]:
    all_files = list(root.glob('**/*.py'))
    gitignore_path = root / '.gitignore'
    if gitignore_path.is_file() and GITIGNORE_AVAILABLE:
        try:
            matches = parse_gitignore(gitignore_path, root)
            return [f for f in all_files if not matches(f)]
        except Exception as e:
            logger.warning(f"Failed to parse .gitignore: {e}")
    return all_files

def analyze_project(project_path_str: str) -> Tuple[Dict[str, Dict], List[str]]:
    project_path = Path(project_path_str)
    logs = [f"Searching for Python files in {project_path}..."]
    python_files = _get_python_files(project_path)
    logs.append(f"Found {len(python_files)} Python files to analyze.")
    
    all_functions = {}
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
                visitor = FunctionCallVisitor(source_code=code, file_path=py_file)
                visitor.visit(ast.parse(code))
                all_functions.update(visitor.functions)
        except Exception as e:
            logs.append(f"[Warning] Could not process {py_file}: {e}")

    return {name: asdict(info) for name, info in all_functions.items()}, logs

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
        if not GENAI_AVAILABLE: raise CodeAnalysisError("Google Generative AI library not installed.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def _generate_summary(self, func_info: Dict) -> str:
        prompt = f"Analyze this Python function and provide a concise, one-sentence summary of its purpose, starting with a verb.\n\n```python\n{func_info['source_code']}\n```"
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                response = await loop.run_in_executor(executor, lambda: self.model.generate_content(prompt))
            return response.text.strip().replace('*', '') or "Failed to generate summary."
        except Exception as e:
            return f"AI summary failed: {e}"

    async def enrich_graph(self, call_graph: Dict) -> List[str]:
        logs = ["--- 🧠 Starting AI Documentation ---"]
        tasks = {name: self._generate_summary(info) for name, info in call_graph.items()}
        summaries = await asyncio.gather(*tasks.values())
        for (name, info), summary in zip(call_graph.items(), summaries):
            info['summary'] = summary
            logs.append(f"  - Generated docs for '{name}'")
        return logs

async def enrich_with_ai_summaries_async(call_graph: Dict, api_key: str) -> List[str]:
    if not api_key: return ["Skipping AI enrichment: No API key provided."]
    try:
        return await AIDocumenter(api_key).enrich_graph(call_graph)
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
