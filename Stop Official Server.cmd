@echo off
setlocal
title Beyond Heroes - Stop Official Server
cd /d "%~dp0"
if errorlevel 1 exit /b 1

echo Stopping the official Beyond Heroes server and saving a backup...
echo.
python -m server.control stop
set "server_result=%errorlevel%"
echo.
if "%server_result%"=="0" goto done

echo The server could not be stopped. Read the message above.
echo Logs are in "%~dp0server\data\logs".

:done
echo.
pause
exit /b %server_result%
