@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup.bat first.
  pause
  exit /b 1
)
echo Starting the voice app... (first start downloads the model and takes a few minutes)
".venv\Scripts\python.exe" app.py
pause
