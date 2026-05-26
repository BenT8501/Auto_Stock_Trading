@echo off
cd /d "%~dp0"
python review_agent\gemma_review_agent.py --project-root .
echo.
echo Review report: outputs\reports\gemma_review.md
pause
