@echo off
setlocal
cd /d "%~dp0"
start "" wscript.exe "%~dp0Start SignBridge.vbs"
exit /b 0

