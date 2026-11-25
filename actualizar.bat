@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m pip install -U yt-dlp
".venv\Scripts\python.exe" -m yt_dlp --version
pause