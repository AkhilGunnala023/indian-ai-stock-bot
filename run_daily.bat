@echo off
REM ================================
REM Indian AI Stock Bot - Daily Run
REM ================================

REM Go to project root
cd /d D:\Akhil\Pycharm\indian-ai-stock-bot-day1

REM Activate virtual environment
call .venv\Scripts\activate

REM Run the daily pipeline
python scripts\run_daily_pipeline.py

REM Pause only if run manually (optional)
REM pause
