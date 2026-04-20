import asyncio
from pathlib import Path
from typing import Dict, Literal, Optional, Tuple

from codegrapher.analyzer import (
    analyze_project,
    build_call_graph,
    enrich_with_ai_summaries_async,
    generate_interactive_diagram_data
)

def get_call_graph(
    project_dir: str = ".", 
    entry_file: Optional[str] = None, 
    entry_func: Optional[str] = None, 
    api_key: Optional[str] = None,
    mode: Literal["flow", "file", "project"] = "project",
    max_depth: int = 10,
    target: str = "human"
) -> Tuple[Dict, Dict]:
    """
    Analyzes the project and returns the raw call_graph dictionary and the diagram data.
    Modes:
    - 'flow': Traces execution from an entry point.
    - 'file': Returns only functions within the entry file.
    - 'project': Returns all functions in the project.
    """
    project_path = Path(project_dir)
    if not project_path.is_dir():
        raise ValueError(f"Invalid or missing project directory: {project_dir}")
    
    all_funcs, logs = analyze_project(project_dir)
    
    if mode == "project":
        call_graph = all_funcs
    else:
        if not entry_file:
            raise ValueError(f"entry_file is required for mode '{mode}'")
        
        entry_points = []
        if entry_func:
            if entry_func in all_funcs:
                entry_points.append(entry_func)
            else:
                raise ValueError(f"Entry function '{entry_func}' not found in the project.")
        else:
            entry_file_path = str((project_path / entry_file).resolve())
            entry_points = [
                name for name, data in all_funcs.items() 
                if Path(data['file_path']).resolve() == Path(entry_file_path).resolve()
            ]

        if not entry_points:
            raise ValueError(f"No functions found for the specified entry point in '{entry_file}'.")
        
        if mode == "file":
            call_graph = {name: data for name, data in all_funcs.items() if name in entry_points}
        else:
            # mode == "flow"
            call_graph = build_call_graph(all_funcs, entry_points, max_depth=max_depth)
    
    if api_key:
        # Run async function synchronously
        asyncio.run(enrich_with_ai_summaries_async(call_graph, api_key, target=target))
        
    diagram_data = generate_interactive_diagram_data(call_graph)
    
    return call_graph, diagram_data
