import pytest
from pathlib import Path
from codegrapher.core import get_call_graph

FIXTURE_DIR = str(Path(__file__).parent / "fixtures")

def test_get_call_graph_project_mode():
    graph, diagram = get_call_graph(project_dir=FIXTURE_DIR, mode="project")
    assert "func_a" in graph
    assert "main" in graph
    assert "DummyClass.method_one" in graph
    
def test_get_call_graph_file_mode():
    graph, diagram = get_call_graph(
        project_dir=FIXTURE_DIR, 
        entry_file="dummy_project.py", 
        mode="file"
    )
    assert "func_a" in graph
    assert "DummyClass.method_two" in graph

def test_get_call_graph_flow_mode():
    # Start from main, we should reach func_a, func_b, DummyClass.method_one, DummyClass.method_two
    graph, diagram = get_call_graph(
        project_dir=FIXTURE_DIR, 
        entry_file="dummy_project.py", 
        entry_func="main",
        mode="flow"
    )
    assert "main" in graph
    assert "func_a" in graph
    
    # Flow from func_a directly
    graph, diagram = get_call_graph(
        project_dir=FIXTURE_DIR, 
        entry_file="dummy_project.py", 
        entry_func="func_a",
        mode="flow"
    )
    assert "func_a" in graph
    assert "func_b" in graph
    assert "main" not in graph # Because flow goes DOWN from func_a
