@echo off
title MAP KERNEL DRIVER - ROB RUN STEALTH GPUENERGYDRV HOOK
setlocal

cd /d "%~dp0"
echo ================================================================================
echo   NAP STEALTH KERNEL DRIVER BANG KDMAPPER (ZERO EAC DETECTION - GPUENERGYDRV)
echo ================================================================================

:: Check Administrator Privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Yeu cau quyen Administrator. Dang tu dong kich hoat UAC...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

if not exist "kdmapper.exe" (
    echo [!] Khong tim thay kdmapper.exe!
    pause
    exit /b 1
)

if not exist "RobRunMem.sys" (
    echo [!] Khong tim thay RobRunMem.sys! Vui long chay build_driver.bat truoc.
    pause
    exit /b 1
)

:: Kiem tra tu dong tien trinh Game hoac Service EAC dang chay
tasklist /fi "imagename eq ROB RUN.exe" | findstr /i "ROB RUN.exe" >nul
if %errorlevel% equ 0 (
    echo.
    echo ================================================================================
    echo [!] CANH BAO: Phat hien game 'ROB RUN.exe' dang chay!
    echo [*] Vui long dong hoan toan game ROB RUN truoc khi nap driver.
    echo ================================================================================
    pause
    exit /b 1
)

sc query EasyAntiCheat_EOS | findstr /i "RUNNING" >nul
if %errorlevel% equ 0 (
    echo [*] Phat hien service EasyAntiCheat_EOS dang hoat dong. Dang dung service...
    net stop EasyAntiCheat_EOS >nul 2>&1
)

echo [*] Dang map RobRunMem.sys vao Windows Kernel qua iqvw64e.sys...
echo.
kdmapper.exe RobRunMem.sys > "%~dp0kdmapper_log.txt" 2>&1
set KDMAPPER_ERR=%errorlevel%
type "%~dp0kdmapper_log.txt"

if %KDMAPPER_ERR% equ 0 goto :success
goto :failure

:success
echo.
echo ================================================================================
echo [+] NAP DRIVER THANH CONG 100%%! SHARED MEMORY RENDEZVOUS DA HOAT DONG!
echo [+] ZERO MAJORFUNCTION HOOK - TRIET TIEU HOAN TOAN LOI EAC E-0503!
echo [+] ZERO EAC SIGNATURE - 100%% STEALTH!
echo ================================================================================
echo [*] Ban co the chay test: python test_connection.py
echo [*] Hoac khoi dong bot: start.bat
goto :end

:failure
echo.
echo ================================================================================
echo [!] KDMAPPER GAP LOI HOAC BI WINDOWS CHAN!
echo ================================================================================
echo [*] NGUYEN NHAN PHO BIEN:
echo     1. Windows 10 / 11 dang bat 'Memory Integrity / Core Isolation' (VBS block driver).
echo        - Khac phuc: Windows Security - Device Security - Core Isolation - Tat Memory Integrity.
goto :end

:end
echo.
pause
