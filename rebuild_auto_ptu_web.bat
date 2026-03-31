@echo off
setlocal enableextensions
pushd "%~dp0"

set "PY=python"
set "LOGDIR=%~dp0build_logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set "STAGE_DIST=%~dp0dist_build"
set "STAGE_WORK=%~dp0build\AutoPTUWeb-stage"
set "FINAL_APP=%~dp0dist\AutoPTUWeb"
set "STAGED_APP=%STAGE_DIST%\AutoPTUWeb"

for /f %%i in ('powershell -NoProfile -Command "(Get-Date -Format \"yyyyMMdd-HHmmss\")"') do set "TS=%%i"
set "LOGFILE=%LOGDIR%\pyinstaller-web-%TS%.log"

echo [1/3] Running web verification tests...
%PY% -m pytest tests/test_web_regressions.py tests/test_battle_state.py tests/test_hazard_moves.py tests/test_csv_repository.py -q
if errorlevel 1 goto :fail

echo [2/3] Closing running AutoPTUWeb instances and rebuilding package...
taskkill /F /IM AutoPTUWeb.exe >nul 2>&1
if exist "%STAGE_DIST%" (
  rmdir /s /q "%STAGE_DIST%" >nul 2>&1
)
if exist "%STAGE_WORK%" (
  rmdir /s /q "%STAGE_WORK%" >nul 2>&1
)
echo Writing PyInstaller log to "%LOGFILE%"
%PY% -m PyInstaller --clean -y --distpath "%STAGE_DIST%" --workpath "%STAGE_WORK%" "%~dp0AutoPTUWeb.spec" > "%LOGFILE%" 2>&1
if errorlevel 1 goto :fail

%PY% "%~dp0scripts\sync_packaged_web_runtime.py" "%STAGED_APP%\_internal\auto_ptu"
if errorlevel 1 goto :fail

echo [3/3] Writing packaged build stamp...
set "GIT_SHA=unknown"
for /f %%i in ('git rev-parse --short HEAD 2^>nul') do set "GIT_SHA=%%i"
(
  echo AutoPTUWeb packaged build
  echo Built: %DATE% %TIME%
  echo Git: %GIT_SHA%
  echo Source static root: auto_ptu\api\static
  echo Rebuild command: rebuild_auto_ptu_web.bat
) > "%STAGED_APP%\BUILD_INFO.txt"

if exist "%FINAL_APP%" (
  rmdir /s /q "%FINAL_APP%" >nul 2>&1
)
if exist "%FINAL_APP%" goto :fail_replace

move "%STAGED_APP%" "%FINAL_APP%" >nul 2>&1
if not exist "%FINAL_APP%\AutoPTUWeb.exe" goto :fail_replace

echo Build complete. Launch from "%FINAL_APP%\AutoPTUWeb.exe"
popd
exit /b 0

:fail_replace
echo Failed to replace "%FINAL_APP%". AutoPTUWeb may still be locked.
echo See "%LOGFILE%" for packaging output if step 2 started.
popd
exit /b 1

:fail
echo Build failed. See "%LOGFILE%" for packaging output if step 2 started.
popd
exit /b 1
