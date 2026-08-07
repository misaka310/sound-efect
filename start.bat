@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo setup.bat を先に実行してください。 & pause & exit /b 1)
start "Sound + BGM Generator" http://127.0.0.1:8600/
.venv\Scripts\python.exe -m app.main --host 127.0.0.1 --port 8600
