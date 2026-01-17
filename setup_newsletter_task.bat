@echo off
REM Setup Windows Task Scheduler for Audience Newsletter
REM Runs Mon/Wed/Sat at 12:00 PM CT (Noon) - matches PB/LA draw schedule

echo ============================================
echo   AUDIENCE NEWSLETTER SCHEDULER SETUP
echo   Schedule: Mon/Wed/Sat at 12:00 PM CT
echo ============================================
echo.

REM Delete existing tasks if they exist
schtasks /delete /tn "AudienceNewsletter_Mon" /f 2>nul
schtasks /delete /tn "AudienceNewsletter_Wed" /f 2>nul
schtasks /delete /tn "AudienceNewsletter_Sat" /f 2>nul

REM Create Monday task
schtasks /create /tn "AudienceNewsletter_Mon" /tr "pythonw \"%~dp0daily_publish.bat\"" /sc weekly /d MON /st 12:00 /ru "%USERNAME%" /rl HIGHEST

REM Create Wednesday task
schtasks /create /tn "AudienceNewsletter_Wed" /tr "pythonw \"%~dp0daily_publish.bat\"" /sc weekly /d WED /st 12:00 /ru "%USERNAME%" /rl HIGHEST

REM Create Saturday task
schtasks /create /tn "AudienceNewsletter_Sat" /tr "pythonw \"%~dp0daily_publish.bat\"" /sc weekly /d SAT /st 12:00 /ru "%USERNAME%" /rl HIGHEST

echo.
echo SUCCESS! Audience newsletter scheduled for:
echo   - Monday at 12:00 PM CT
echo   - Wednesday at 12:00 PM CT
echo   - Saturday at 12:00 PM CT
echo.
echo This matches Powerball/Lotto America draw schedules!
echo.
echo ============================================
echo   COMMANDS
echo ============================================
echo To verify:  schtasks /query /tn "AudienceNewsletter_Mon"
echo To run now: schtasks /run /tn "AudienceNewsletter_Mon"
echo To delete all:
echo   schtasks /delete /tn "AudienceNewsletter_Mon" /f
echo   schtasks /delete /tn "AudienceNewsletter_Wed" /f
echo   schtasks /delete /tn "AudienceNewsletter_Sat" /f
echo.
pause
