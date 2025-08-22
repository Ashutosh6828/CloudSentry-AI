@echo off
ECHO "--- Activating Virtual Environment and Running Pipeline ---"

REM Navigate to the script's directory
cd /d "%~dp0"

REM Activate the virtual environment
call .\venv\Scripts\activate.bat

REM Run the Python scripts in order
python ingest_logs.py
python preprocess.py
python detector.py

ECHO "--- Pipeline Run Complete ---"