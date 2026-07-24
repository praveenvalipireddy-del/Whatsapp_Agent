@echo off
REM ===== Start the WhatsApp bench-sales agent locally =====
REM Double-click this file (or run it) to launch both the server and the tunnel.
REM Two windows open: one for the webhook server, one for ngrok. Keep both open.
REM Close either window to stop the agent.

cd /d "%~dp0"

echo Starting webhook server on port 8000...
start "WhatsApp Agent - Server" cmd /k python -m uvicorn app:app --host 0.0.0.0 --port 8000

timeout /t 3 /nobreak >nul

echo Starting ngrok tunnel...
set "NGROK=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"
if not exist "%NGROK%" set "NGROK=ngrok"
start "WhatsApp Agent - ngrok" cmd /k "%NGROK%" http 8000

echo.
echo ============================================================
echo  Both started. The ngrok window shows your public URL
echo  (https://smugness-dismantle-lethargy.ngrok-free.dev).
echo  That URL is already set in Meta, so nothing to change.
echo.
echo  To review pending vendor drafts, open a new terminal here
echo  and run:  python review.py
echo ============================================================
echo.
pause
