@echo off
cd /d "%~dp0"
python broker_check.py --asset domestic --symbol 005930
pause
