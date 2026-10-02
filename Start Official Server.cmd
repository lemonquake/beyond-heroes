@echo off
setlocal
title Beyond Heroes - Start Official Server
cd /d "%~dp0"
if errorlevel 1 exit /b 1

echo Starting the official Beyond Heroes server...
echo.
python -m server.control start %*
set "server_result=%errorlevel%"
echo.
if not "%server_result%"=="0" goto failed

echo You can close this window. The server stays running in the background.
echo To stop it and save a backup, double-click "Stop Official Server.cmd".
goto done

:failed
echo The server could not be started. Read the message above.
echo Logs are in "%~dp0server\data\logs".

:done
echo.
pause
exit /b %server_result%
