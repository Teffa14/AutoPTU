@echo off
setlocal
set "ROOT=%~dp0"
set "STAGE_DIST=%ROOT%dist_build"
set "STAGE_WORK=%ROOT%build\AutoPTUTerrainMapper-stage"
set "FINAL_APP=%ROOT%dist\AutoPTUTerrainMapper"
set "STAGED_APP=%STAGE_DIST%\AutoPTUTerrainMapper"

echo [1/3] Running web verification tests...
python -m pytest tests/test_web_regressions.py -q || goto :fail

echo [2/3] Closing running AutoPTUTerrainMapper instances and rebuilding package...
taskkill /F /IM AutoPTUTerrainMapper.exe >nul 2>&1
if exist "%STAGE_DIST%" rmdir /S /Q "%STAGE_DIST%"
if exist "%STAGE_WORK%" rmdir /S /Q "%STAGE_WORK%"
python -m PyInstaller --clean -y --distpath "%STAGE_DIST%" --workpath "%STAGE_WORK%" "%ROOT%AutoPTUTerrainMapper.spec" || goto :fail

echo [3/3] Replacing packaged output...
if exist "%FINAL_APP%" rmdir /S /Q "%FINAL_APP%"
move "%STAGED_APP%" "%FINAL_APP%" >nul || goto :fail
echo Build complete. Launch from "%FINAL_APP%\AutoPTUTerrainMapper.exe"
exit /b 0

:fail
echo Build failed.
exit /b 1
