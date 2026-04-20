import pytest
from pathlib import Path
from codegrapher.analyzer import analyze_project
from codegrapher.parsers.python import PythonParser

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "dummy_project.py"

def test_tree_sitter_parsing():
    with open(FIXTURE_PATH, "r") as f:
        code = f.read()
        
    parser = PythonParser(source_code=code, file_path=FIXTURE_PATH)
    funcs = parser.parse()
    
    # Check that functions are identified
    assert "func_a" in funcs
    assert "func_b" in funcs
    assert "DummyClass.method_one" in funcs
    assert "main" in funcs
    
    # Check signature extraction
    # Tree-sitter might extract signatures slightly differently than AST
    assert "x: int, y: int = 10" in funcs["func_a"]['signature']
    assert "val" in funcs["func_b"]['signature']
    assert "self" in funcs["DummyClass.method_one"]['signature']
    
    # Check docstring extraction
    assert "This is function A." in funcs["func_a"]['docstring']
    
    # Check calls
    assert "func_b" in funcs["func_a"]['calls']
    assert "func_a" in funcs["DummyClass.method_one"]['calls']
    assert "method_two" in funcs["DummyClass.method_one"]['calls']
    
def test_analyze_project():
    funcs, logs = analyze_project(str(Path(__file__).parent / "fixtures"))
    assert "func_a" in funcs
    # The new JS test file will also be picked up, so there are > 5 functions now
    assert len(funcs) >= 5 
