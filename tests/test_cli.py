import pytest
import os
from pathlib import Path
from codegrapher.cli import app
from typer.testing import CliRunner
from unittest.mock import patch

FIXTURE_DIR = str(Path(__file__).parent / "fixtures")
runner = CliRunner()

def test_cli_config():
    with patch('keyring.set_password') as mock_set:
        result = runner.invoke(app, ["config", "--model", "gemini", "--api-key", "test-key"])
        assert result.exit_code == 0
        assert "Successfully stored API key" in result.stdout
        mock_set.assert_called_with("codegrapher", "gemini", "test-key")

@patch('keyring.get_password', return_value=None)
def test_cli_context(mock_keyring, tmp_path):
    output_file = str(tmp_path / "test_graph.md")
    
    result = runner.invoke(app, ["context", FIXTURE_DIR, "--mode", "project", "-o", output_file])
        
    assert result.exit_code == 0
    assert os.path.exists(output_file)
    with open(output_file, "r") as f:
        content = f.read()
        assert "func_a" in content
        assert "DummyClass" in content
        assert "graph TD" in content

@patch('keyring.get_password', return_value=None)
def test_cli_vis(mock_keyring, tmp_path):
    output_file = str(tmp_path / "test_graph.html")
    
    with patch('webbrowser.open') as mock_browser:
        result = runner.invoke(app, ["vis", FIXTURE_DIR, "-e", "dummy_project.py", "--mode", "file", "-o", output_file])
        if result.exit_code != 0:
            print(result.stdout)
            print(result.exception)
        assert result.exit_code == 0
        mock_browser.assert_called_once()
            
    assert os.path.exists(output_file)
    with open(output_file, "r") as f:
        content = f.read()
        assert "var data" in content or "vis.Network" in content or "vis-network" in content
        assert "func_a" in content
