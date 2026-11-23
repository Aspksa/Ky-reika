@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title KYUREIKA - Core and SQLite

set "PYTHON_CMD="
where py >nul 2>&1
if not errorlevel 1 (
    py -3 -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3"
)
if not defined PYTHON_CMD (
    where python >nul 2>&1
    if not errorlevel 1 (
        python -c "import sys" >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=python"
    )
)
if not defined PYTHON_CMD (
    echo Python 3 not found. Install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)
%PYTHON_CMD% main.py init
if errorlevel 1 (
    echo Failed to initialize KYUREIKA SQLite database.
    pause
    exit /b 1
)
:MENU
echo.
echo ========================================
echo          KYUREIKA - CORE
echo ========================================
echo 1. Status
echo 2. Memories
echo 3. Personality context
echo 4. Add memory
echo 5. Exit
choice /c 12345 /n /m "Choose [1-5]: "
if errorlevel 5 goto END
if errorlevel 4 goto REMEMBER
if errorlevel 3 goto CONTEXT
if errorlevel 2 goto MEMORIES
if errorlevel 1 goto STATUS
goto MENU
:STATUS
%PYTHON_CMD% main.py status
goto MENU
:MEMORIES
%PYTHON_CMD% main.py memories
goto MENU
:CONTEXT
%PYTHON_CMD% main.py context
goto MENU
:REMEMBER
set "MEMORY_TEXT="
set /p "MEMORY_TEXT=Memory text: "
if not defined MEMORY_TEXT goto MENU
%PYTHON_CMD% main.py remember "%MEMORY_TEXT%"
goto MENU
:END
endlocal
exit /b 0
