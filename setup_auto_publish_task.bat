@echo off
REM Setup Windows Task Scheduler for Newsletter Auto-Publish
REM Runs Mon/Wed/Sat at 12:00 PM CT (Noon)

echo ============================================
echo  NEWSLETTER AUTO-PUBLISH SCHEDULER SETUP
echo ============================================
echo.

REM Delete existing task if it exists
schtasks /delete /tn "LotteryNewsletterPublish" /f 2>nul

REM Create task for Monday at Noon
schtasks /create /tn "LotteryNewsletterPublish" /tr "pythonw \"%~dp0auto_publish.py\"" /sc weekly /d MON /st 12:00 /f

REM Add Wednesday trigger
schtasks /change /tn "LotteryNewsletterPublish" /tr "pythonw \"%~dp0auto_publish.py\""

echo.
echo Creating additional triggers for Wed and Sat...

REM Use PowerShell to add multiple triggers
powershell -Command "$task = Get-ScheduledTask -TaskName 'LotteryNewsletterPublish'; $triggers = @(); $triggers += New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 12:00PM; $triggers += New-ScheduledTaskTrigger -Weekly -DaysOfWeek Wednesday -At 12:00PM; $triggers += New-ScheduledTaskTrigger -Weekly -DaysOfWeek Saturday -At 12:00PM; Set-ScheduledTask -TaskName 'LotteryNewsletterPublish' -Trigger $triggers"

echo.
echo ============================================
echo  SETUP COMPLETE!
echo ============================================
echo.
echo Newsletter will auto-publish to:
echo   https://www.princessupload.net/lottery-newsletter.html
echo.
echo Schedule: Mon/Wed/Sat at 12:00 PM CT (Noon)
echo.
echo To test now, run: python auto_publish.py
echo.
pause
