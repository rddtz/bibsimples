@echo off
title bibsimples
cd /d "%~dp0backend"

echo Iniciando bibsimples...
start "" venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8765

timeout /t 3 /nobreak >nul
start http://localhost:8765
