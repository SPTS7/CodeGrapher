import os
from typing import Optional

from codegrapher.core import get_call_graph

def generate_markdown(
    project_dir: str = ".", 
    entry_file: Optional[str] = None, 
    entry_func: Optional[str] = None, 
    output_file: str = "context_for_agents.md",
    api_key: Optional[str] = None,
    mode: str = "project",
    max_depth: int = 10
) -> str:
    """
    Generates a Markdown file with a Mermaid graph and function summaries.
    This is highly optimized for AI agents to read and understand code context.
    """
    call_graph, _ = get_call_graph(
        project_dir, 
        entry_file=entry_file, 
        entry_func=entry_func, 
        api_key=api_key, 
        mode=mode, 
        max_depth=max_depth,
        target="ai"
    )
    
    md_lines = []
    md_lines.append("# Project Call Graph Analysis")
    md_lines.append(f"\n**Project Directory:** `{os.path.abspath(project_dir)}`")
    md_lines.append(f"**Analysis Mode:** `{mode}`")
    if entry_file:
        md_lines.append(f"**Entry File:** `{entry_file}`")
    if entry_func:
        md_lines.append(f"**Entry Function:** `{entry_func}`")
        
    md_lines.append("\n## Call Graph (Mermaid)")
    md_lines.append("```mermaid")
    md_lines.append("graph TD")
    
    # Extract classes for grouping
    classes = {}
    for func_name in call_graph:
        if '.' in func_name:
            cls, _ = func_name.split('.', 1)
            if cls not in classes: classes[cls] = []
            classes[cls].append(func_name)
    
    # Track edges
    edges = set()
    for func_name, info in call_graph.items():
        if '.' not in func_name:
            md_lines.append(f"    {func_name}")
        for called in info.get("calls", []):
            if called in call_graph:
                edge = f"    {func_name} --> {called}"
                if edge not in edges:
                    md_lines.append(edge)
                    edges.add(edge)
                    
    for cls, funcs in classes.items():
        md_lines.append(f"    subgraph {cls}")
        for f in funcs:
            md_lines.append(f"        {f}[\"{f.split('.')[-1]}\"]")
        md_lines.append("    end")
    
    md_lines.append("```")
    
    md_lines.append("\n## Function Details")
    
    # Group details by class or top-level
    details_grouped = {"Top-Level": []}
    for func_name, info in call_graph.items():
        if '.' in func_name:
            cls, _ = func_name.split('.', 1)
            if cls not in details_grouped: details_grouped[cls] = []
            details_grouped[cls].append((func_name, info))
        else:
            details_grouped["Top-Level"].append((func_name, info))
            
    for group, funcs in details_grouped.items():
        if not funcs: continue
        if group != "Top-Level":
            md_lines.append(f"\n### Class: `{group}`")
        else:
            md_lines.append(f"\n### Top-Level Functions")
            
        for func_name, info in funcs:
            sig = info.get('signature', '')
            name_display = func_name.split('.')[-1] if group != "Top-Level" else func_name
            try:
                rel_path = os.path.relpath(info.get('file_path'), start=project_dir)
            except Exception:
                rel_path = info.get('file_path')
                
            md_lines.append(f"- **`{name_display}({sig})`** `[{rel_path}:{info.get('line_number')}]` (Cplx: {info.get('complexity')})")
            
            if info.get('summary') and info.get('summary') != "No AI summary generated.":
                md_lines.append(f"  - AI: {info.get('summary')}")
            
            if info.get('docstring'):
                doc = info['docstring'].replace('\\n', '\n').strip()
                first_para = doc.split('\n\n')[0].replace('\n', ' ')
                if first_para:
                    md_lines.append(f"  - Doc: {first_para}")
                
    content = "\n".join(md_lines)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Markdown graph generated at: {output_file}")
    return output_file
