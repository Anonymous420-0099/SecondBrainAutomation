@echo off
REM ============================================================
REM YouTube Second Brain — Windows Task Scheduler Setup
REM ============================================================
REM This script creates a scheduled task that runs the pipeline
REM daily at midnight (00:00).
REM
REM Run this script ONCE as Administrator to set up the schedule.
REM ============================================================

echo.
echo ============================================================
echo   YouTube Second Brain - Task Scheduler Setup
echo ============================================================
echo.

REM --- Configuration ---
set TASK_NAME=YouTubeSecondBrain
set PROJECT_DIR=%~dp0
set PYTHON_SCRIPT=%PROJECT_DIR%main.py

REM Find Python executable
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in PATH.
    echo Please install Python 3.10+ and add it to your PATH.
    pause
    exit /b 1
)

REM Get the full Python path
for /f "delims=" %%i in ('where python') do set PYTHON_PATH=%%i
echo Found Python: %PYTHON_PATH%
echo Project dir:  %PROJECT_DIR%
echo.

REM --- Create the scheduled task ---
echo Creating scheduled task "%TASK_NAME%"...
echo Schedule: Daily at 00:00 (midnight)
echo.

schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%PYTHON_PATH%\" \"%PYTHON_SCRIPT%\"" ^
    /sc daily ^
    /st 00:00 ^
    /f ^
    /rl HIGHEST

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo   [SUCCESS] Scheduled task created!
    echo.
    echo   Task name: %TASK_NAME%
    echo   Schedule:  Daily at midnight (00:00)
    echo   Action:    python main.py
    echo.
    echo   To view:   Open Task Scheduler and find "%TASK_NAME%"
    echo   To delete: schtasks /delete /tn "%TASK_NAME%" /f
    echo   To run now: schtasks /run /tn "%TASK_NAME%"
    echo ============================================================
) else (
    echo.
    echo [ERROR] Failed to create scheduled task.
    echo Try running this script as Administrator.
)

echo.

REM --- Create a "run now" shortcut script ---
echo Creating run_now.bat...
(
    echo @echo off
    echo echo Running YouTube Second Brain pipeline...
    echo cd /d "%PROJECT_DIR%"
    echo "%PYTHON_PATH%" "%PYTHON_SCRIPT%"
    echo echo.
    echo echo Pipeline complete. Press any key to close.
    echo pause
) > "%PROJECT_DIR%run_now.bat"

echo Created run_now.bat — double-click to run the pipeline manually.
echo.
pause
