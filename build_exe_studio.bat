@echo off
cd /d "%~dp0"
echo.
echo === Building Web Novel Studio .exe ===
echo.

pip install pyinstaller 2>nul

pyinstaller --onefile --console --name "Web Novel Studio" --icon=generator\static\favicon.ico launcher_studio.py

echo.
if exist "dist\Web Novel Studio.exe" (
    echo Build complete!
    echo.
    echo EXE is at:  dist\Web Novel Studio.exe
    echo.
    copy "dist\Web Novel Studio.exe" "Web Novel Studio.exe" >nul 2>nul
    echo Also copied to: Web Novel Studio.exe
) else (
    echo Build failed. Check errors above.
)
echo.
pause
