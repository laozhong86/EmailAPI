@echo off
chcp 65001 > nul
echo ===== Email App Packaging Script =====

REM Set variables
set OUTPUT_NAME=emailAPI.exe
set SKIP_INSTALL=0

REM Parse command line arguments
if "%1"=="--skip-install" set SKIP_INSTALL=1
if not "%2"=="" set OUTPUT_NAME=%2

echo Output file: %OUTPUT_NAME%
echo Project root: %CD%

REM Get version number
set VERSION=0.0.0
for /f "tokens=2 delims='""" %%a in ('type __version__.py ^| findstr __version__') do (
    set VERSION=%%a
)
echo Current version: %VERSION%

REM Install dependencies
if "%SKIP_INSTALL%"=="0" (
    echo.
    echo Installing dependencies...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    echo Dependencies installation complete
)

REM Start packaging
echo.
echo Starting packaging...
set PYINSTALLER_CMD=pyinstaller --clean --onefile --name="%OUTPUT_NAME%" 
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --add-data="__version__.py;." 
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --add-data=".env.example;."

REM Add config.ini.example if exists
if exist config.ini.example (
    set PYINSTALLER_CMD=%PYINSTALLER_CMD% --add-data="config.ini.example;."
)

REM Add missing modules and DLLs to fix runtime errors
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --hidden-import=xml.parsers.expat
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --collect-all=xml
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --collect-all=email

REM Try to locate Anaconda DLLs and add them
for %%D in (libexpat.dll libssl-3-x64.dll libcrypto-3-x64.dll) do (
    if exist "C:\ProgramData\anaconda3\Library\bin\%%D" (
        set PYINSTALLER_CMD=%PYINSTALLER_CMD% --add-binary="C:\ProgramData\anaconda3\Library\bin\%%D;."
    )
)

REM Add main program and output directory
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --distpath="dist" "main.py"

echo Executing command: %PYINSTALLER_CMD%
%PYINSTALLER_CMD%

REM Check packaging result
if exist "dist\%OUTPUT_NAME%" (
    echo Packaging successful: %CD%\dist\%OUTPUT_NAME%
    
    REM Calculate SHA-256 hash
    certutil -hashfile "dist\%OUTPUT_NAME%" SHA256 > "dist\%OUTPUT_NAME%.sha256"
    echo SHA-256 hash saved to: %CD%\dist\%OUTPUT_NAME%.sha256
    
    REM Display file size
    for %%F in ("dist\%OUTPUT_NAME%") do (
        set SIZE=%%~zF
        echo File size: %%~zF bytes
        
        REM Calculate size in MB
        set /a SIZE_MB=%%~zF / 1048576
        echo File size: !SIZE_MB! MB
        
        REM Check if file size exceeds limit
        if !SIZE_MB! GTR 150 (
            echo Warning: File size exceeds 150MB limit
        )
    )
) else (
    echo Packaging failed: Output file not found
    exit /b 1
)

echo.
echo ===== Packaging complete =====
