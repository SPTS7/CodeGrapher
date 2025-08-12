#!/bin/bash
# This script sets up and runs the AI Code Visualizer application.

# Check if the virtual environment directory exists.
if [ ! -d "CodeGrapher_Venv" ]; then
    echo "--- Creating virtual environment..."
    python3 -m venv CodeGrapher_Venv

    echo "--- Activating virtual environment and installing dependencies..."
    source CodeGrapher_Venv/bin/activate
    pip install -r requirements.txt
else
    echo "--- Activating existing virtual environment..."
    source CodeGrapher_Venv/bin/activate
fi

echo "--- Starting the application..."
echo "--- Open http://127.0.0.1:5000/ in your browser if it doesn't open automatically."
python3 app.py
