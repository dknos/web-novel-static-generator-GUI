@echo off
cd /d "%~dp0"
python gradio_studio.py
if errorlevel 1 pause
