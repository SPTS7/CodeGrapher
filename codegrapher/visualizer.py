import json
import os
import tempfile
import webbrowser
from typing import Optional
import importlib.resources

from codegrapher.core import get_call_graph

def visualize(
    project_dir: str = ".", 
    entry_file: Optional[str] = None, 
    entry_func: Optional[str] = None, 
    api_key: Optional[str] = None,
    output_file: Optional[str] = "codegraph.html",
    mode: str = "project",
    max_depth: int = 10
) -> str:
    """
    Generates a static HTML file containing an interactive call graph and opens it in the browser.
    """
    _, diagram_data = get_call_graph(
        project_dir, 
        entry_file=entry_file, 
        entry_func=entry_func, 
        api_key=api_key, 
        mode=mode, 
        max_depth=max_depth
    )
    
    # Load HTML template
    try:
        html_template = importlib.resources.read_text("codegrapher.templates", "codegraph.html")
    except Exception as e:
        raise RuntimeError(f"Could not load HTML template: {e}")
        
    html_content = html_template.replace("${DIAGRAM_DATA}", json.dumps(diagram_data))
    
    if output_file is None:
        fd, output_file = tempfile.mkstemp(suffix=".html", prefix="codegrapher_")
        os.close(fd)
        
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    import sys
    import io
    
    # Silence noisy KDE/xdg-open warnings on Linux by temporarily redirecting stderr at the OS level
    try:
        fd = sys.stderr.fileno()
        saved_fd = os.dup(fd)
        devnull = os.open(os.devnull, os.O_WRONLY)
        
        try:
            os.dup2(devnull, fd)
            webbrowser.open(f"file://{os.path.abspath(output_file)}")
        finally:
            os.dup2(saved_fd, fd)
            os.close(devnull)
            os.close(saved_fd)
    except (AttributeError, io.UnsupportedOperation):
        # Happens during testing when sys.stderr is mocked
        webbrowser.open(f"file://{os.path.abspath(output_file)}")
        
    print(f"Visualization generated at: {output_file}")
    return output_file
