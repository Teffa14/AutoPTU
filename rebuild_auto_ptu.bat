@echo off
set "KEEP_OPEN=1"
set "RELAUNCHED_FLAG=0"
for %%A in (%*) do (
    if /I "%%~A"=="/nokeep" (
        set "KEEP_OPEN=0"
    ) else if /I "%%~A"=="/relaunched" (
        set "RELAUNCHED_FLAG=1"
    )
)
if "%RELAUNCHED_FLAG%"=="0" if "%KEEP_OPEN%"=="1" (
    set "AUTO_PTU_REBUILD_RELAUNCHED=1"
    "%COMSPEC%" /k ""%~f0" %* /relaunched"
    exit /b
)
setlocal enableextensions
pushd "%~dp0"
set "LOGDIR=%~dp0build_logs"
if not exist "%LOGDIR%" (
    mkdir "%LOGDIR%"
)
set "PY=python"
set "FOUNDATION=%~dp0Foundry\ptr2e-Stable\ptr2e-Stable\packs\core-moves"
set "NO_PAUSE=0"
if /I "%~1"=="/nowait" set "NO_PAUSE=1"

echo Refreshing compiled PTU data...
%PY% -m auto_ptu.tools.build_data
if NOT "%ERRORLEVEL%"=="0" (
    echo [error] Compiled data refresh failed.
    if "%NO_PAUSE%"=="0" pause>nul
    popd
    exit /b %ERRORLEVEL%
)

if exist "%FOUNDATION%" (
    echo Regenerating keyword demos from Foundry data...
    %PY% -m auto_ptu.tools.generate_keyword_demos
    if NOT "%ERRORLEVEL%"=="0" (
        echo [error] Keyword demo generation failed.
        if "%NO_PAUSE%"=="0" pause>nul
        popd
        exit /b %ERRORLEVEL%
    )
) else (
    echo [warning] Foundry move pack missing; skipping keyword demo regeneration.
)

echo Syncing frontend static assets to dist targets...
%PY% "%~dp0scripts\sync_frontend_assets.py"
if NOT "%ERRORLEVEL%"=="0" (
    echo [error] Frontend asset sync failed.
    if "%NO_PAUSE%"=="0" pause>nul
    popd
    exit /b %ERRORLEVEL%
)

echo Generating trainer runtime coverage report...
%PY% -m auto_ptu.tools.generate_trainer_coverage_report
if NOT "%ERRORLEVEL%"=="0" (
    echo [error] Trainer runtime coverage report generation failed.
    if "%NO_PAUSE%"=="0" pause>nul
    popd
    exit /b %ERRORLEVEL%
)

for /f %%i in ('powershell -NoProfile -Command "(Get-Date -Format \"yyyyMMdd-HHmmss\")"') do set "TS=%%i"
set "LOGFILE=%LOGDIR%\pyinstaller-%TS%.log"
echo Writing build log to "%LOGFILE%"
%PY% -m PyInstaller --clean "%~dp0AutoPTU.spec" > "%LOGFILE%" 2>&1
set "ERR=%ERRORLEVEL%"
if NOT "%ERR%"=="0" (
    echo Build failed. See "%LOGFILE%" for details.
    if "%NO_PAUSE%"=="0" pause>nul
    popd
    exit /b %ERR%
)
echo Build complete. Output available in "%~dp0dist".
if "%NO_PAUSE%"=="0" (
    echo Press any key to close this window...
    pause>nul
)
popd
exit /b 0
