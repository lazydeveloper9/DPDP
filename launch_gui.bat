@echo off
title CS-01 DPDP Compliance Auditor
cd /d "%~dp0"
if exist "dist\CS-01\cs01-gui.exe" (
    start "" "dist\CS-01\cs01-gui.exe" %*
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m cs01.gui %*
) else (
    python -m cs01.gui %*
)
if errorlevel 1 pause
