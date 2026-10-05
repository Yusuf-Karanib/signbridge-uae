@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo SignBridge is not set up yet.
  echo Right-click setup.ps1 and choose "Run with PowerShell" first.
  pause
  exit /b 1
)
echo This diagnostic window stays open so startup errors remain visible.
".venv\Scripts\python.exe" app.py
if errorlevel 1 pause
