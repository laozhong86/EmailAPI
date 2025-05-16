@echo off
setlocal enabledelayedexpansion

REM Error handling setup
REM Note: Remove "@echo off" to see each command execution
REM Email Application Launcher
REM This script activates the virtual environment and runs the Email application

echo Starting Email Application...

REM Set the project root directory (the directory where this batch file is located)
set PROJECT_ROOT=%~dp0
cd %PROJECT_ROOT%

REM Check if Python is installed
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.6 or higher and try again.
    pause
    exit /b 1
)

REM Check if virtual environment exists, if not create it
if not exist "%PROJECT_ROOT%venv\Scripts\activate.bat" (
    echo Virtual environment not found. Creating new virtual environment...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment.
        echo Please install venv module with: pip install virtualenv
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call "%PROJECT_ROOT%venv\Scripts\activate.bat"

REM Install required packages
echo Checking and installing required packages...

REM First try to install essential packages
echo Installing essential packages first...

REM Install Flask and all its dependencies
pip install Flask==2.3.3 --no-cache-dir
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install Flask. Trying without version constraint...
    pip install Flask --no-cache-dir
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install Flask. Please check your internet connection.
        pause
        exit /b 1
    )
)

REM Install other essential packages
pip install python-dotenv requests beautifulsoup4 chardet
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install essential packages.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

REM Then try to install other packages, but allow partial failures
echo Installing remaining packages...
pip install -r requirements.txt --no-deps
REM Continue execution even if some packages fail to install

REM Ensure critical packages are installed
echo Verifying critical dependencies...

REM Check python-dotenv
pip show python-dotenv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: python-dotenv package is missing. Attempting to install it...
    pip install python-dotenv
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install python-dotenv, which is required for the application.
        pause
        exit /b 1
    )
)

REM Check werkzeug (critical dependency for Flask)
pip show werkzeug >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: werkzeug package is missing. Attempting to install it...
    pip install werkzeug
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install werkzeug, which is required for Flask.
        pause
        exit /b 1
    )
)

REM Check other critical dependencies for Flask
for %%p in (click itsdangerous jinja2 markupsafe) do (
    pip show %%p >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo WARNING: %%p package is missing. Attempting to install it...
        pip install %%p
    )
)

REM Create log directory
if not exist "%PROJECT_ROOT%logs" mkdir "%PROJECT_ROOT%logs"

REM Set log filename (using current date and time)
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "LOGDATE=%dt:~0,8%-%dt:~8,6%"
set "LOGFILE=%PROJECT_ROOT%logs\email_app_%LOGDATE%.log"

REM Run application and redirect output to log file
echo Running Email application...
echo Log file: %LOGFILE%
echo.
echo Starting application at %date% %time% > "%LOGFILE%"

REM Run application in try-catch mode
echo Attempting to run Email application... >> "%LOGFILE%"

REM Use >nul 2>&1 to hide command itself but still show command output
>nul 2>&1 (
    python "%PROJECT_ROOT%main.py" 2>> "%LOGFILE%"
    set ERRORLEVEL_PYTHON=%ERRORLEVEL%
)

REM Check Python program exit code
if %ERRORLEVEL_PYTHON% NEQ 0 (
    echo ERROR: Application exited with code %ERRORLEVEL_PYTHON% >> "%LOGFILE%"
    echo.
    echo Application encountered an error (exit code: %ERRORLEVEL_PYTHON%).
    echo Please check the log file for details: %LOGFILE%
    echo.
    echo Displaying last 10 lines of log file:
    echo -------------------------------
    powershell -Command "Get-Content -Path '%LOGFILE%' -Tail 10"
    echo -------------------------------
    echo.
    echo Press any key to exit...
    pause > nul
)

REM If the application exits, properly deactivate the virtual environment
if exist "%PROJECT_ROOT%venv\Scripts\deactivate.bat" (
    call "%PROJECT_ROOT%venv\Scripts\deactivate.bat"
) else (
    REM Fallback if deactivate.bat doesn't exist
    set PATH=%PATH:venv\Scripts;=%
    set VIRTUAL_ENV=
)

echo Email application has been closed.
pause
