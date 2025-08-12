@echo off
REM This script sets up and runs the AI Code Visualizer application.

REM Check if the virtual environment directory exists.
IF NOT EXIST CodeGrapher_Venv (
    echo --- Creating virtual environment...
    python -m venv CodeGrapher_Venv
    
    echo --- Activating virtual environment and installing dependencies...
    call CodeGrapher_Venv\Scripts\activate.bat
    pip install -r requirements.txt
) ELSE (
    echo --- Activating existing virtual environment...
    call CodeGrapher_Venv\Scripts\activate.bat
)

echo --- Starting the application...
echo --- Open http://127.0.0.1:5000/ in your browser if it doesn't open automatically.
python app.py

pause
