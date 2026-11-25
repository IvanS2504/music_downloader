@echo off
cd /d "%~dp0"
start "Servidor" /min ".venv\Scripts\python.exe" manage.py runserver --noreload
timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:8000