@echo off
setlocal
title Clipo - Auto-clip, auto-viral

cd /d "%~dp0"
call .venv\Scripts\activate.bat
python main_improved.py
echo.
pause