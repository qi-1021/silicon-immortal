@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" tools\bootstrap.py %*
) else (
  py -3.12 tools\bootstrap.py %*
)
if errorlevel 1 (
  echo.
  echo Startup failed. Install Python 3.12, then run this file again.
  echo See docs\guide\install.md for details.
  pause
  exit /b 1
)
