<div align="center">

# AI CodeGrapher

**Generate token-optimized context maps of Polyglot repositories for AI coding agents.**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

</div>

---

## The Problem: Bloated Context Windows

Feeding a large codebase to an LLM (like Claude, GPT-4, or Gemini) usually means dumping raw source code into the prompt. This rapidly exhausts the context window, wastes thousands of tokens, and drowns the AI in implementation details when it just needs to understand the architecture.

## The Solution: CodeGrapher

**CodeGrapher** solves this by abstracting your codebase into a dense, semantic **Context Map**. 

Instead of passing raw files, CodeGrapher uses **Tree-sitter** and the Gemini API to natively parse your code, extract function signatures, execution flow, and concise AI-generated summaries into a highly optimized Markdown file with Mermaid diagrams. 

Your AI assistant gets a perfect blueprint of the codebase, using a fraction of the tokens.

### Key Features
* **Cross-Platform**: Works flawlessly on **Linux, macOS, and Windows** (available as a standalone binary or Python package).
* **Multi-Language Support**: Natively parses **Python, JavaScript, and TypeScript** (`.py`, `.js`, `.jsx`, `.ts`, `.tsx`). 
* **Token-Optimized Context Maps (`cg context`)**: Feed your AI a structured map of the exact execution flow, skipping irrelevant code bodies.
* **Three Analysis Scopes**:
  * `flow`: Trace execution from a specific entry point (e.g., `main.py`). The ultimate way to understand how a request propagates.
  * `file`: Isolate and map only the functions inside a single file.
  * `project`: Scan and map the entire codebase architecture.
* **Smart AI Caching:** CodeGrapher caches AST parses and Gemini API summaries locally. Subsequent runs are completely instantaneous.
* **[Bonus] Interactive Visuals (`cg vis`)**: For humans! Instantly open a zoomable, click-to-view-source network diagram in your browser.

---

## Installation

You can install CodeGrapher either as a standalone binary (no Python required) or as a Python package.

### Option 1: Standalone Binary (Recommended)
If you don't have Python installed, or just want a clean global executable:

**Mac / Linux:**
```sh
curl -fsSL https://raw.githubusercontent.com/SPTS7/CodeGrapher/main/install.sh | bash
```
*(Windows users can download the `.exe` directly from the [Releases page](https://github.com/SPTS7/CodeGrapher/releases)).*

### Option 2: Python Package (Developers)
If you have Python 3.9+ installed:

1. **Clone the repository:**
   ```sh
   git clone https://github.com/SPTS7/CodeGrapher.git
   cd CodeGrapher
   ```

2. **Install the package locally:**
   ```sh
   pip install -e .
   ```

### Uninstall
If you installed the standalone binary, you can easily remove it (and its local cache) by running:
```sh
cg uninstall
```
If you installed via Python/pip, you can remove it with:
```sh
pip uninstall codegrapher
```

---

## Usage (CLI)

Once installed, use the `cg` command. It defaults to analyzing the current directory (`.`) in `project` mode.

### 1. Generating AI Context Maps
Create a `.md` file to feed into your AI assistant. To get AI-generated function summaries, you need to provide an API key. 
You can securely store it using the built-in config command:
```sh
cg config --api-key YOUR_API_KEY
```
*(Alternatively, you can set the `MODEL_API_KEY` environment variable).*

```sh
# Map the entire codebase (outputs to codegraph.md)
cg context

# Map only a specific file
cg context . -e utils.py --mode file -o utils_context.md

# Trace execution flow from main.py
cg context . -e main.py --mode flow --max-depth 5
```

### 2. [Bonus] Interactive Visualizations
Create an interactive, premium dark-mode HTML graph that opens automatically in your browser.

```sh
# Visualize the entire codebase
cg vis

# Visualize execution flow from main.py
cg vis . -e main.py --mode flow
```

---

## Usage (Python API)

Automate documentation or create self-updating AI context files in your CI/CD pipelines.

```python
from codegrapher import generate_markdown, visualize

# Generate AI Context
generate_markdown(
    project_dir="./my_project",
    mode="project",
    output_file="codebase_context.md",
    api_key="YOUR_KEY"
)

# Generate HTML Visual
visualize(
    project_dir="./my_project",
    entry_file="main.py",
    mode="flow",
    max_depth=5
)
```

---

## Roadmap

* [ ] Add support for Go and Java.
* [ ] Support for filtering out standard library calls automatically.
* [ ] Integrate with OpenAI/Anthropic APIs alongside Gemini.

---

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.
