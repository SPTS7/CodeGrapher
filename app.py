import eel
import asyncio
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import logging
import sys

# Import your existing analysis library
import analyzer_lib as analyzer

# --- EEL Setup ---
# Initialize Eel with the 'web' folder as the root for UI files
eel.init('web')

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Log to standard output
)
logger = logging.getLogger(__name__)


# --- Functions Exposed to JavaScript ---

@eel.expose
def browse_for_folder():
    """
    Opens a native OS dialog to select a folder.
    This function is called from the 'Browse' button in the UI.
    """
    logger.info("Opening folder selection dialog...")
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window
    root.attributes('-topmost', True)  # Bring the dialog to the front
    folder_path = filedialog.askdirectory(master=root)
    root.destroy()
    
    if folder_path:
        logger.info(f"Folder selected: {folder_path}")
        return folder_path
    else:
        logger.warning("No folder selected.")
        return None

@eel.expose
def analyze_project_and_visualize(project_dir, entry_file, entry_func, api_key):
    """
    The main analysis function called from the JavaScript frontend.
    It orchestrates the analysis, AI enrichment, and data generation.
    """
    try:
        # --- 1. Input Validation ---
        if not project_dir or not Path(project_dir).is_dir():
            raise ValueError(f"Invalid or missing project directory: {project_dir}")
        if not entry_file:
            raise ValueError("Entry file is required.")

        project_path = Path(project_dir)
        
        # --- 2. Static Code Analysis ---
        logger.info(f"Starting analysis of project at: {project_path}")
        eel.update_loading_message("Scanning project files...")
        
        # The analyzer library returns all functions found in the project
        all_funcs, logs = analyzer.analyze_project(project_dir)
        logger.info(f"Analysis found {len(all_funcs)} total functions.")
        
        # --- 3. Determine Entry Points for the Graph ---
        eel.update_loading_message("Determining entry points...")
        entry_points = []
        if entry_func:
            if entry_func in all_funcs:
                entry_points.append(entry_func)
            else:
                raise ValueError(f"Entry function '{entry_func}' not found in the project.")
        else:
            # If no function is specified, use all functions in the entry file
            entry_file_path = str((project_path / entry_file).resolve())
            entry_points = [
                name for name, data in all_funcs.items() 
                if Path(data['file_path']).resolve() == Path(entry_file_path).resolve()
            ]

        if not entry_points:
            raise ValueError(f"No functions found for the specified entry point in '{entry_file}'.")
        
        logger.info(f"Building call graph from {len(entry_points)} entry points...")
        
        # --- 4. Build the Call Graph ---
        eel.update_loading_message("Building call graph...")
        call_graph = analyzer.build_call_graph(all_funcs, entry_points)
        
        # --- 5. Enrich with AI Summaries (if API key is provided) ---
        if api_key:
            logger.info("Enriching with AI summaries...")
            eel.update_loading_message("Generating AI summaries...")
            # Run the async AI enrichment function
            ai_logs = asyncio.run(analyzer.enrich_with_ai_summaries_async(call_graph, api_key))
            logs.extend(ai_logs)
        
        # --- 6. Generate Data for Visualization ---
        logger.info("Generating data for interactive diagram...")
        eel.update_loading_message("Creating visualization...")
        diagram_data = analyzer.generate_interactive_diagram_data(call_graph)
        logs.append("\nInteractive diagram data generated successfully.")
        
        logger.info("Analysis complete. Sending data to frontend.")
        return {'status': 'success', 'diagramData': diagram_data, 'logs': "\n".join(logs)}

    except Exception as e:
        logger.exception("An error occurred during analysis.")
        return {'status': 'error', 'message': str(e)}

# --- Application Start ---
if __name__ == '__main__':
    # This block now correctly handles browser fallbacks.
    try:
        # Attempt to start with Chrome first.
        logger.info("Attempting to launch with Chrome...")
        eel.start('index.html', mode='chrome', size=(1400, 900), block=True)
    except (IOError, SystemError):
        logger.warning("Chrome not found. Attempting to launch with Firefox...")
        try:
            # If Chrome fails, try Firefox.
            eel.start('index.html', mode='firefox', size=(1400, 900), block=True)
        except (IOError, SystemError) as e:
            logger.error(f"Could not launch in Chrome or Firefox. Error: {e}")
            logger.info("Attempting to launch with your system's default browser...")
            # As a last resort, try the default system browser.
            eel.start('index.html', size=(1400, 900), block=True)
