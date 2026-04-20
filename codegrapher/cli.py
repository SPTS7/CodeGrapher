import os
from typing import Optional
import typer
from rich.console import Console
from codegrapher import visualize, generate_markdown
import keyring

app = typer.Typer(
    help="CodeGrapher CLI - Generate token-optimized context maps of Python repositories for AI coding agents.",
    rich_markup_mode="rich",
    no_args_is_help=True
)
console = Console()

def resolve_api_key(api_key: Optional[str] = None, model: str = "gemini") -> Optional[str]:
    """Resolves the API key from CLI args, environment variables, or keyring."""
    if api_key:
        return api_key
    
    env_key = os.environ.get("MODEL_API_KEY")
    if env_key:
        return env_key
        
    try:
        return keyring.get_password("codegrapher", model.lower())
    except Exception:
        return None

@app.command()
def config(
    model: str = typer.Option("gemini", "--model", help="The model provider to configure (e.g., gemini)."),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="The API key to securely store.")
):
    """
    Securely store an API key for a specific AI model.
    """
    if not api_key:
        api_key = typer.prompt("Enter your API key", hide_input=True)
        
    try:
        keyring.set_password("codegrapher", model.lower(), api_key)
        console.print(f"[bold green]Successfully stored API key for {model} securely![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to securely store API key: {e}[/bold red]")

@app.command()
def uninstall():
    """
    Uninstall CodeGrapher (removes the executable and local cache).
    """
    import sys
    import shutil
    from pathlib import Path
    
    # Remove local cache
    cache_dir = Path(".codegraph_cache")
    if cache_dir.exists() and cache_dir.is_dir():
        try:
            shutil.rmtree(cache_dir)
            console.print("[green]Removed local cache directory.[/green]")
        except Exception as e:
            console.print(f"[red]Failed to remove local cache directory: {e}[/red]")
    
    # Also check for the old cache file just in case
    old_cache = Path(".codegrapher_cache.json")
    if old_cache.exists():
        try:
            old_cache.unlink()
        except Exception:
            pass
            
    # Try to find the executable
    executable_path = shutil.which("cg")
    
    if not executable_path:
        console.print("[yellow]Could not find 'cg' executable in PATH. If installed via pip, please run 'pip uninstall codegrapher'.[/yellow]")
        return
        
    # Check if installed via pip (rudimentary check: if it's in a python site-packages or bin directory inside venv)
    if "site-packages" in executable_path or "venv" in executable_path or ".pyenv" in executable_path or not executable_path.endswith('cg'):
        console.print("[yellow]It looks like CodeGrapher was installed via pip or a virtual environment.[/yellow]")
        console.print("Please use [bold]pip uninstall codegrapher[/bold] to remove it completely.")
        return

    # Assuming standalone binary
    try:
        os.remove(executable_path)
        console.print(f"[green]Successfully removed CodeGrapher executable from {executable_path}.[/green]")
    except Exception as e:
        console.print(f"[red]Failed to remove executable: {e}[/red]")
        console.print(f"You may need to manually run: sudo rm {executable_path}")

@app.command()
def context(
    project_dir: str = typer.Argument(
        ".", 
        help="Path to the project directory."
    ),
    entry_file: Optional[str] = typer.Option(
        None, 
        "--entry-file", "-e", 
        help="Main entry file (e.g., main.py). Required for 'flow' and 'file' modes."
    ),
    entry_func: Optional[str] = typer.Option(
        None, 
        "--entry-func", "-f", 
        help="Specific entry function (optional)."
    ),
    api_key: Optional[str] = typer.Option(
        None, 
        "--api-key", "-k", 
        help="API Key for AI summaries (defaults to MODEL_API_KEY env var or secure keyring)."
    ),
    mode: str = typer.Option(
        "project", 
        "--mode", "-m", 
        help="Analysis mode: 'flow', 'file', or 'project'."
    ),
    max_depth: int = typer.Option(
        10, 
        "--max-depth", "-d", 
        help="Maximum depth for 'flow' mode."
    ),
    output_file: Optional[str] = typer.Option(
        "context_for_agents.md", 
        "--output", "-o", 
        help="Output Markdown file."
    )
):
    """
    Generate a [bold green]token-optimized Context Map[/bold green] for your AI assistant.
    Saves context window space by abstracting code into a semantic graph.
    """
    try:
        resolved_key = resolve_api_key(api_key)
        output_path = generate_markdown(
            project_dir=project_dir,
            entry_file=entry_file,
            entry_func=entry_func,
            api_key=resolved_key,
            output_file=output_file,
            mode=mode,
            max_depth=max_depth
        )
        
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            tokens = len(content) // 4
            console.print(f"[bold blue]Estimated AI Tokens:[/bold blue] ~{tokens:,}")
        except Exception:
            pass
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def vis(
    project_dir: str = typer.Argument(
        ".", 
        help="Path to the project directory."
    ),
    entry_file: Optional[str] = typer.Option(
        None, 
        "--entry-file", "-e", 
        help="Main entry file (e.g., main.py). Required for 'flow' and 'file' modes."
    ),
    entry_func: Optional[str] = typer.Option(
        None, 
        "--entry-func", "-f", 
        help="Specific entry function (optional)."
    ),
    api_key: Optional[str] = typer.Option(
        None, 
        "--api-key", "-k", 
        help="API Key for AI summaries (defaults to MODEL_API_KEY env var or secure keyring)."
    ),
    mode: str = typer.Option(
        "project", 
        "--mode", "-m", 
        help="Analysis mode: 'flow', 'file', or 'project'."
    ),
    max_depth: int = typer.Option(
        10, 
        "--max-depth", "-d", 
        help="Maximum depth for 'flow' mode."
    ),
    output_file: Optional[str] = typer.Option(
        "codegraph.html", 
        "--output", "-o", 
        help="Output HTML file."
    )
):
    """
    [Bonus feature] Generate an interactive [bold cyan]HTML visualization[/bold cyan] of your codebase.
    """
    try:
        resolved_key = resolve_api_key(api_key)
        visualize(
            project_dir=project_dir,
            entry_file=entry_file,
            entry_func=entry_func,
            api_key=resolved_key,
            output_file=output_file,
            mode=mode,
            max_depth=max_depth
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
