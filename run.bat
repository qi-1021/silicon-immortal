@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" tools\bootstrap.py %*
) else (
  where py >nul 2>&1
  if not errorlevel 1 (
    py -3.12 tools\bootstrap.py %*
  ) else (
    python tools\bootstrap.py %*
  )
)
if errorlevel 1 (
  echo.
  echo Startup failed. Install Python 3.12, then run this file again.
  echo See docs\guide\install.md for details.
  pause
  exit /b 1
)
