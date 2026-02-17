@echo off
cd /d "%~dp0"
echo.
echo === Building Web Novel App .exe ===
echo.

pip install pyinstaller 2>nul

pyinstaller --onefile --windowed --name "Web Novel App" --icon=generator\static\favicon.ico launcher.py

echo.
if exist "dist\Web Novel App.exe" (
    echo Build complete!
    echo.
    echo EXE is at:  dist\Web Novel App.exe
    echo.
    echo Copy it into this project folder to use it.
    copy "dist\Web Novel App.exe" "Web Novel App.exe" >nul 2>nul
    echo Also copied to: Web Novel App.exe
) else (
    echo Build failed. Check errors above.
)
echo.
pause
