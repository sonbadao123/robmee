@echo off
setlocal
echo ================================================================================
echo   NAP / KHOI CHAY KERNEL DRIVER CHO ROB RUN (EAC EOS BYPASS)
echo ================================================================================

set "SYS_PATH=%~dp0RobRunMem.sys"
set "SERVICE_NAME=RobRunDriver"

if not exist "%SYS_PATH%" (
    echo [!] Khong tim thay file RobRunMem.sys trong thu muc nay!
    echo [*] Hay build driver hoac su dung mapper de nap file sys vao kernel truoc.
    pause
    exit /b 1
)

echo [*] Kiem tra quyen Administrator...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Vui long chay file bat nay bang quyen Run as Administrator!
    pause
    exit /b 1
)

echo [*] Dang tao va khoi chay Service kernel: %SERVICE_NAME%...
sc stop %SERVICE_NAME% >nul 2>&1
sc delete %SERVICE_NAME% >nul 2>&1
sc create %SERVICE_NAME% type= kernel binPath= "%SYS_PATH%"
sc start %SERVICE_NAME%

if %errorlevel% equ 0 (
    echo [+] Driver da duoc nap thanh cong vao Windows Kernel!
    echo [+] Thiet bi \\.\RobRunMem da san sang cho Python Client ket noi.
) else (
    echo [!] Khong the start driver truc tiep qua sc.exe vi Windows bat buoc chu ky so (DSE).
    echo [*] GIAI PHAP: Su dung BYOVD / KdMapper de map truc tiep RobRunMem.sys vao Ring 0 ma khong can chu ky so.
)

pause
