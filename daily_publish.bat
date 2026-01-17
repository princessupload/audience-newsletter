@echo off
REM Daily Newsletter Publisher - Run this daily to update and publish newsletter
REM Can be scheduled via Windows Task Scheduler

cd /d "%~dp0"

echo ============================================
echo   DAILY LOTTERY NEWSLETTER PUBLISHER
echo   %date% %time%
echo ============================================

echo.
echo Step 1: Updating lottery data and jackpots...
python update_data.py

echo.
echo Step 2: Generating newsletter...
python generate_newsletter.py

echo.
echo Step 3: Publishing newsletter...
python publish_newsletter.py --email

echo.
echo ============================================
echo   COMPLETE!
echo ============================================
echo.
echo Newsletter saved to: output\latest.html
echo Embed snippet saved to: output\embed_snippet.html
echo.
pause
