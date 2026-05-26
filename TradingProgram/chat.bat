@echo off
cd /d "%~dp0"
python review_agent\chat.py --project-root .
pause
