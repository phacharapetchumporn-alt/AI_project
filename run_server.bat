@echo off
chcp 65001 > nul
title SignSubs AI Web Server

echo =========================================================
echo    SignSubs AI Server - Starting Backend...
echo =========================================================

set PYTHON_PATH="C:\Users\User\AppData\Local\Python\bin\python.exe"

if exist %PYTHON_PATH% (
    %PYTHON_PATH% app.py %*
) else (
    python app.py %*
)

pause
