
@echo off

cd /d "%~dp0"

call venv\Scripts\activate.bat

python asistente_v2.py

pause
