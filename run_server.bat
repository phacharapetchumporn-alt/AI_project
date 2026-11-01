@echo off
chcp 65001 > nul
title SignSubs AI Web Server

echo =========================================================
echo    SignSubs AI Server - Starting Backend...
echo =========================================================

cd /d "%~dp0"

where python3.12 >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Starting with python3.12...
    python3.12 app.py %*
    goto :done
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Starting with py -3.12...
    py -3.12 app.py %*
    goto :done
)

set PYTHON_PATH="C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe"
if exist %PYTHON_PATH% (
    echo [INFO] Starting with Microsoft WindowsApps Python 3.12...
    %PYTHON_PATH% app.py %*
    goto :done
)

echo [INFO] Starting with default python...
python app.py %*

:done
pause
