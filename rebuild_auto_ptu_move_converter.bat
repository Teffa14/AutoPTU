@echo off
setlocal enableextensions
pushd "%~dp0"
set "LOGDIR=%~dp0build_logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
for /f %%i in ('powershell -NoProfile -Command "(Get-Date -Format \"yyyyMMdd-HHmmss\")"') do set "TS=%%i"
set "LOGFILE=%LOGDIR%\pyinstaller-move-converter-%TS%.log"
echo Writing build log to "%LOGFILE%"
python -m PyInstaller --clean "%~dp0AutoPTUMoveConverter.spec" > "%LOGFILE%" 2>&1
set "ERR=%ERRORLEVEL%"
if NOT "%ERR%"=="0" (
    echo Build failed. See "%LOGFILE%" for details.
    popd
    exit /b %ERR%
)
echo Build complete. Output available in "%~dp0dist".
popd
exit /b 0
