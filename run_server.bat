@echo off
chcp 65001 > nul
title SignSubs AI Web Server

echo =========================================================
echo    SignSubs AI Server - Starting Backend...
echo =========================================================

set PYTHON_312="C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe"

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Starting with Python 3.12 (py -3.12)...
    py -3.12 app.py %*
) else if exist %PYTHON_312% (
    echo [INFO] Starting with Python 3.12...
    %PYTHON_312% app.py %*
) else (
    echo [INFO] Starting with default python...
    python app.py %*
)

pause
