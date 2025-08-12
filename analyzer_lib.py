import ast
import os
from pathlib import Path
import json
import base64
import time

# Dependencies
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from gitignore_parser import parse_gitignore
except ImportError:
    parse_gitignore = None


class FunctionCallVisitor(ast.NodeVisitor):
    """AST visitor to find function definitions and their calls."""
    def __init__(self):
        self.functions = {}
        self.current_function = None
        self.current_file = None

    def visit_FunctionDef(self, node):
        self.current_function = node.name
        self.functions[node.name] = {
            "calls": [],
            "source_code": ast.get_source_segment(self.source_code, node),
            "file_path": str(self.current_file.resolve()),
            "summary": "No summary generated."
        }
        self.generic_visit(node)
        self.current_function = None

    def visit_Call(self, node):
        if self.current_function:
            call_name = ast.unparse(node.func)
            self.functions[self.current_function]["calls"].append(call_name)
        self.generic_visit(node)

    def analyze(self, code, file_path):
        self.source_code = code
        self.current_file = file_path
        try:
            tree = ast.parse(code)
            self.visit(tree)
        except SyntaxError as e:
            print(f"    [Warning] Could not parse {file_path} due to SyntaxError: {e}")


def analyze_project(project_path):
    """
    Analyzes all Python files in a given project directory, respecting .gitignore.
    """
    visitor = FunctionCallVisitor()
    root = Path(project_path)
    
    # --- .gitignore parsing ---
    gitignore_path = root / '.gitignore'
    matches = None
    if gitignore_path.is_file() and parse_gitignore is not None:
        matches = parse_gitignore(gitignore_path, root)
    
    all_files = list(root.glob('**/*.py'))
    python_files = []
    if matches:
        # Filter out ignored files
        python_files = [f for f in all_files if not matches(f)]
    else:
        python_files = all_files

    log_messages = [f"Found {len(python_files)} Python files to analyze..."]
    
    for py_file in python_files:
        log_messages.append(f"  - Analyzing {py_file.relative_to(root)}")
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                code = f.read()
                visitor.analyze(code, py_file)
        except Exception as e:
            log_messages.append(f"    [Warning] Could not read or process {py_file}: {e}")
            
    return visitor.functions, log_messages


def build_call_graph(all_functions, entry_points):
    """Builds a specific call graph starting from one or more entry points."""
    functions_to_include = set()
    queue = list(entry_points)
    processed = set()
    while queue:
        current_func_name = queue.pop(0)
        if current_func_name in processed:
            continue
        processed.add(current_func_name)
        if current_func_name in all_functions:
            functions_to_include.add(current_func_name)
            for called_func in all_functions[current_func_name]['calls']:
                queue.append(called_func)
    return {name: data for name, data in all_functions.items() if name in functions_to_include}


def get_ai_summary(model, source_code):
    """Sends source code to the Gemini model and returns a summary."""
    prompt = f"""
    You are an expert Python programmer creating documentation. 
    Analyze the following Python function and provide a concise, one-sentence summary of its primary purpose. 
    Do not describe the parameters or return values. Start the sentence with a verb.

    ```python
    {source_code}
    ```
    """
    try:
        response = model.generate_content(prompt)
        summary = response.text.strip().replace('*', '')
        return summary
    except Exception as e:
        return f"AI summary failed: {e}"


def enrich_with_ai_summaries(call_graph, api_key):
    """Iterates through the call graph and adds AI-generated summaries."""
    log_messages = ["\n--- 🧠 Starting AI Documentation Generation ---"]
    if not genai:
        log_messages.append("Skipping AI enrichment because 'google-generativeai' is not installed.")
        return log_messages

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        log_messages.append(f"Error configuring Gemini API: {e}")
        return log_messages

    for i, (func_name, data) in enumerate(call_graph.items()):
        log_messages.append(f"  - Generating docs for '{func_name}' ({i+1}/{len(call_graph)})...")
        summary = get_ai_summary(model, data['source_code'])
        data['summary'] = summary
        time.sleep(1)
    
    return log_messages


def generate_interactive_diagram_data(call_graph):
    """
    Generates a data structure for the interactive vis.js diagram.
    """
    nodes = []
    edges = []
    
    # Assign a color to each file for node styling
    file_colors = {}
    color_palette = ['#fde74c', '#ff5964', '#38618c', '#42f2f5', '#f28a42', '#8a42f2']
    color_index = 0

    for func_name, data in call_graph.items():
        file_path = data['file_path']
        if file_path not in file_colors:
            file_colors[file_path] = color_palette[color_index % len(color_palette)]
            color_index += 1

        nodes.append({
            'id': func_name,
            'label': func_name,
            'title': data.get('summary', 'No summary generated.'), # Tooltip
            'color': file_colors[file_path],
            'source_code': data.get('source_code', '# Source not found')
        })
        
        for called_func in data['calls']:
            if called_func in call_graph:
                edges.append({
                    'from': func_name,
                    'to': called_func,
                    'arrows': 'to'
                })
                
    return {'nodes': nodes, 'edges': edges}

