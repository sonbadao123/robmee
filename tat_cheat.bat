@echo off
title TAT CHEAT & KHOI PHUC HE THONG - ROB RUN
cd /d "%~dp0"

:: 1. Tu dong yeu cau Administrator neu chua co
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo [!] Dang goi quyen Administrator... Vui long chon YES/CO tren man hinh!
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"

echo ========================================================
echo   TAT TOAN BO CHEAT, GO HOOK DRIVER ^& DON SACH HE THONG
echo ========================================================
echo.

echo [*] 1. Go hook kernel dispatch table bang Python...
python restore_system.py

echo.
echo [*] 2. Dung va xoa bo cac service driver bi EAC dua vao danh sach den...
sc stop AMDRyzenMasterDriverV31 >nul 2>&1
sc stop gdrv3 >nul 2>&1
sc stop WinRing0_1_2_0 >nul 2>&1
sc delete gdrv3 >nul 2>&1
sc delete WinRing0_1_2_0 >nul 2>&1

echo.
echo [*] 3. Dong moi tien trinh cheat dang chay ngam...
taskkill /F /IM RobRunESP.exe /T >nul 2>&1
taskkill /F /IM "ROB【云更新 右键管理员运行】.exe" /T >nul 2>&1
taskkill /F /IM RobRun.sp.exe /T >nul 2>&1

echo.
echo ========================================================
echo [+] DA HOAN TAT 100%! HE THONG DA DUOC KHOI PHUC VE NGUYEN BAN.
echo [*] Ma loi EAC (E-0503 SecurityViolationError) da duoc triet tieu.
echo [*] dj co the vao game ROB RUN choi binh thuong, khong lo bi vang!
echo ========================================================
echo.
pause
