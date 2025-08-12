<div align="center">

<!-- LOGO SPOT -->
<img src="web/img/logo.png" alt="Logo" width="120" height="120">

# AI Code Visualizer

**Instantly generate beautiful, AI-documented call graphs from any Python project.**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

</div>

---

## About The Project

The **AI Code Visualizer** is a desktop tool designed to help developers understand complex Python codebases. By simply selecting a project folder, the application performs a static analysis to map out function calls and dependencies. It then renders an interactive, hierarchical graph that you can explore.

What makes this tool unique is its integration with the Gemini API. With an optional API key, it can automatically generate concise, one-sentence summaries for each function, providing instant documentation and making it easier than ever to get a high-level overview of how your code works.

### Key Features

* **Local Project Analysis:** Securely analyze projects on your local machine. No code is ever uploaded.
* **Interactive Call Graphs:** Visualize your code's architecture with a dynamic, zoomable graph powered by `vis.js`.
* **AI-Powered Documentation:** Automatically generate summaries for functions using the Google Gemini API.
* **Source Code Viewer:** Click on any function node in the graph to instantly see its source code.
* **Cross-Platform:** Works on Windows, macOS, and Linux, with support for both Chrome and Firefox.

---

### Screenshot

<!-- SCREENSHOT SPOT -->

![App Screenshot](web/img\site.png)

---

### Built With

This project was built with a combination of powerful front-end and back-end technologies:

* **Python:** The core language for the analysis engine.
* **Eel:** A lightweight library for creating electron-like desktop apps with Python.
* **Google Gemini API:** For generating AI-powered code summaries.
* **HTML5, CSS3, JavaScript:** For the user interface.
* **Bootstrap 5:** For the responsive grid system and UI components.
* **vis.js:** For rendering the interactive network graphs.
* **highlight.js:** For beautiful syntax highlighting in the code viewer.

---

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

You need to have Python 3.9 or newer installed on your system. You can download it from [python.org](https://www.python.org/downloads/).

You will also need either Google Chrome or Mozilla Firefox installed.

### Installation

1. **Clone the repository:**

2. **Navigate to the project directory:**

    ```sh
    cd CodeGrapher
    ```

3. **Install the required Python packages:**

    ```sh
    pip install -r requirements.txt
    ```

---

## Usage

1. **Run the application** from the project's root directory:

    ```sh
    python app.py
    ```

2. **Browse for your project:** Click the "Browse" button to select the root folder of the Python project you want to analyze.
3. **Specify the entry point:**
    * **Entry File:** Enter the name of the main file where your program execution begins (e.g., `main.py`).
    * **Entry Function (Optional):** Enter the name of the specific function you want to start the graph from (e.g., `main`). If you leave this blank, the tool will trace all functions within the specified entry file.
4. **Add your Gemini API Key (Optional):** If you want AI-generated summaries, paste your Gemini API key into the corresponding field. You can get a key from [Google AI Studio](https://aistudio.google.com/app/apikey).
5. **Generate!** Click the "Generate Visualization" button and watch the magic happen.

---

## Roadmap

* [ ] Add support for analyzing projects from a `.zip` file.
* [ ] Implement an "Export to PNG/SVG" feature for the graph.
* [ ] Add a dark mode/light mode toggle for the UI.
* [ ] Improve call detection for dynamically called functions.

---

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

---

## Contact

Project Link
