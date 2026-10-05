@echo off
setlocal
set "ProjectFolder=%~dp0"
for %%I in ("%~dp0..\..") do set "MainProject=%%~fI\"
if not exist "%ProjectFolder%.venv\Scripts\python.exe" if exist "%MainProject%.venv\Scripts\python.exe" set "ProjectFolder=%MainProject%"
cd /d "%ProjectFolder%"
if not exist "%ProjectFolder%.venv\Scripts\python.exe" (
  echo SignBridge is not set up yet.
  echo Folder checked: %ProjectFolder%
  echo Right-click setup.ps1 in that folder and choose "Run with PowerShell" first.
  pause
  exit /b 1
)
echo This diagnostic window stays open so startup errors remain visible.
"%ProjectFolder%.venv\Scripts\python.exe" "%ProjectFolder%app.py"
if errorlevel 1 pause
