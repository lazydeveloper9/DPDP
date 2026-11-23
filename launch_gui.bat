@echo off
title CS-01 DPDP Compliance Auditor
cd /d "%~dp0"

if "%1"=="--dist" (
    if exist "dist\CS-01\cs01-gui.exe" (
        start "" "dist\CS-01\cs01-gui.exe"
        exit /b 0
    )
)

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" -m cs01.gui %*
) else if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" -m cs01.gui %*
) else if exist "dist\CS-01\cs01-gui.exe" (
    start "" "dist\CS-01\cs01-gui.exe" %*
) else (
    start "" python -m cs01.gui %*
)
