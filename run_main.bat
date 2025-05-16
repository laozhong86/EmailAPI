@echo off
REM Simple script to run Email application main.py
REM This script activates the virtual environment before running main.py

echo Starting Email Application...

REM Set the project root directory (the directory where this batch file is located)
set PROJECT_ROOT=%~dp0
cd %PROJECT_ROOT%

REM Check if virtual environment exists
if not exist "%PROJECT_ROOT%venv\Scripts\activate.bat" (
    echo Virtual environment not found at %PROJECT_ROOT%venv
    echo Please run run_email_app.bat first to set up the environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call "%PROJECT_ROOT%venv\Scripts\activate.bat"

REM Create log directory if it doesn't exist
if not exist "%PROJECT_ROOT%logs" mkdir "%PROJECT_ROOT%logs"

REM Set log filename (using current date and time)
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "LOGDATE=%dt:~0,8%-%dt:~8,6%"
set "LOGFILE=%PROJECT_ROOT%logs\email_app_%LOGDATE%.log"

REM Run the Email application
echo Running Email application...
echo Log file: %LOGFILE%
echo.

REM Log start time
echo Starting application at %date% %time% > "%LOGFILE%"

REM Run the application directly (output will be shown in console)
echo Running main.py directly...
echo ----------------------------------------
python "%PROJECT_ROOT%main.py"

REM If the application exits, properly deactivate the virtual environment
if exist "%PROJECT_ROOT%venv\Scripts\deactivate.bat" (
    echo Deactivating virtual environment...
    call "%PROJECT_ROOT%venv\Scripts\deactivate.bat"
) else (
    REM Fallback if deactivate.bat doesn't exist
    set PATH=%PATH:venv\Scripts;=%
    set VIRTUAL_ENV=
)

REM Show exit message
echo.
echo Email application has been closed.
pause
