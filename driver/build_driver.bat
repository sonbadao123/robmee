@echo off
title BIEN DICH KERNEL DRIVER - ROB RUN
echo ================================================================================
echo   BIEN DICH KERNEL DRIVER CHO ROB RUN (AUTO-DETECT TOOLCHAIN)
echo ================================================================================

cd /d "%~dp0"
echo [*] Thu muc lam viec: %~dp0

set "GCC_PATH=C:\Users\vphoa\AppData\Local\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin\gcc.exe"
set "DDK_INC=C:\Users\vphoa\AppData\Local\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\x86_64-w64-mingw32\include\ddk"

if not exist "%GCC_PATH%" goto :no_gcc

echo [+] Da phat hien trinh bien dich MinGW-w64 Native Kernel Toolchain!
echo [*] Dang bien dich driver.c thanh driver.o...
"%GCC_PATH%" -c driver.c -o driver.o -I"%DDK_INC%" -m64 -D_AMD64_ -D_KERNEL_MODE -Wall -Wno-unknown-pragmas
if errorlevel 1 goto :compile_err

echo [*] Dang lien ket driver.o thanh RobRunMem.sys...
"%GCC_PATH%" -Wl,--subsystem,native -Wl,--entry,DriverEntry -Wl,--file-alignment,0x1000 -Wl,--section-alignment,0x1000 -Wl,--image-base,0x10000 -nostartfiles -shared driver.o -o RobRunMem.sys -lntoskrnl -lhal
if errorlevel 1 goto :link_err

if exist driver.o del driver.o >nul 2>&1
echo.
echo ================================================================================
echo [+] BIEN DICH KERNEL DRIVER THANH CONG: RobRunMem.sys
echo ================================================================================
goto :end

:compile_err
echo [!] Loi bien dich driver.c!
goto :end

:link_err
echo [!] Loi lien ket RobRunMem.sys!
goto :end

:no_gcc
echo [!] Khong tim thay gcc.exe. Vui long kiem tra lai duong dan MinGW hoac MSVC WDK.
goto :end

:end
pause
