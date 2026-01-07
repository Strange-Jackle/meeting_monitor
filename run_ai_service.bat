@echo off
REM Ensure we are in the script's directory (project root) then go to ai_service
cd /d "%~dp0ai_service"
echo Starting AI Service from: %CD%
python -m uvicorn app.main:app --reload --port 8000
