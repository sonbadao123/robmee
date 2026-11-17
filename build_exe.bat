@echo off
title BUILD ROBRUN STANDALONE EXE
cd /d "%~dp0"

echo ========================================================
echo   DONG GOI ROB RUN ESP THANH 1 FILE EXE DUY NHAT
echo ========================================================
echo.

python -m PyInstaller --clean --onefile --name "RobRunESP" --uac-admin main.py
if %errorlevel% neq 0 (
    echo [!] Dong goi that bai!
    pause
    exit /b 1
)

copy /y "dist\RobRunESP.exe" "RobRunESP.exe" >nul
echo.
echo ========================================================
echo [+] DONG GOI THANH CONG: RobRunESP.exe (13 MB)
echo [*] File nam ngay tai thu muc goc: d:\ESP robrun\RobRunESP.exe
echo ========================================================
pause
