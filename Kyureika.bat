@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem UTF-8 for Cyrillic file names and Python input/output.
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
title KYUREIKA - Safe Launcher
rem Keep this file beside main.py. Web chat binds to loopback only.
rem Use quoted paths and avoid parenthesized blocks around user-controlled values.
pushd "%~dp0" 2>nul
if errorlevel 1 goto PATH_ERROR
set "ROOT=%CD%"
set "ENTRY=%ROOT%\main.py"
if not exist "%ENTRY%" goto FILE_ERROR
set "SITE=%ROOT%\index.html"
if not exist "%SITE%" goto SITE_ERROR

set "PY_EXE="
set "PY_ARG="
if exist "%ROOT%\.venv\Scripts\python.exe" goto TRY_VENV
where py >nul 2>&1
if not errorlevel 1 goto TRY_PY
goto TRY_PYTHON
:TRY_VENV
"%ROOT%\.venv\Scripts\python.exe" -c "import sys; assert sys.version_info >= (3,10)" >nul 2>&1
if errorlevel 1 goto TRY_PY_LAUNCHER
set "PY_EXE=%ROOT%\.venv\Scripts\python.exe"
goto CHECK_PY
:TRY_PY_LAUNCHER
where py >nul 2>&1
if not errorlevel 1 goto TRY_PY
goto TRY_PYTHON
:TRY_PY
py -3 -c "import sys; assert sys.version_info >= (3,10)" >nul 2>&1
if errorlevel 1 goto TRY_PYTHON
set "PY_EXE=py"
set "PY_ARG=-3"
goto CHECK_PY
:TRY_PYTHON
where python >nul 2>&1
if errorlevel 1 goto PY_ERROR
set "PY_EXE=python"
goto CHECK_PY
:CHECK_PY
"%PY_EXE%" %PY_ARG% -c "import sys; assert sys.version_info >= (3,10)" >nul 2>&1
if errorlevel 1 goto PY_ERROR
"%PY_EXE%" %PY_ARG% "%ENTRY%" init
if errorlevel 1 goto INIT_ERROR
rem Start the local web chat.
call :OPEN_SITE

:MENU
cls
echo ============================================
echo              KYUREIKA CORE
echo ============================================
echo Root: "%ROOT%"
echo.
echo 1. Open website
echo 2. Core status
echo 3. View memories
echo 4. Add memory
echo 5. Personality context
echo 6. Diagnostics
echo 7. Run tests
echo 8. Backup SQLite
echo 9. Exit
echo.
choice /c 123456789 /n /m "Select [1-9]: "
if errorlevel 9 goto EXIT_OK
if errorlevel 8 goto BACKUP
if errorlevel 7 goto TESTS
if errorlevel 6 goto DIAGNOSTICS
if errorlevel 5 goto CONTEXT
if errorlevel 4 goto REMEMBER
if errorlevel 3 goto MEMORIES
if errorlevel 2 goto STATUS
if errorlevel 1 goto WEBSITE
goto MENU

:WEBSITE
call :OPEN_SITE
goto MENU
:OPEN_SITE
start "KYUREIKA Web" "%PY_EXE%" %PY_ARG% "%ROOT%\webapp.py"
if errorlevel 1 echo WARNING: Browser could not open the local website.
exit /b 0
:STATUS
"%PY_EXE%" %PY_ARG% "%ENTRY%" status
goto WAIT_MENU
:MEMORIES
"%PY_EXE%" %PY_ARG% "%ENTRY%" memories
goto WAIT_MENU
:REMEMBER
rem Input is handled by Python, avoiding CMD metacharacter injection.
"%PY_EXE%" %PY_ARG% "%ENTRY%" remember-prompt
goto WAIT_MENU
:CONTEXT
"%PY_EXE%" %PY_ARG% "%ENTRY%" context
goto WAIT_MENU
:DIAGNOSTICS
echo.
echo Python executable:
"%PY_EXE%" %PY_ARG% -c "import sys; print(sys.executable); print(sys.version)"
echo.
echo Project entry: "%ENTRY%"
echo.
echo SQLite integrity:
"%PY_EXE%" %PY_ARG% -c "from core.database import DB_PATH,initialize,connect; initialize(); c=connect(DB_PATH); db=c.__enter__(); print('Database:', DB_PATH); print('Integrity:', db.execute('PRAGMA integrity_check').fetchone()[0]); c.__exit__(None,None,None)"
echo.
echo Network: web chat uses a dynamically assigned loopback port.
echo Close the web server window to stop it.
goto WAIT_MENU
:TESTS
"%PY_EXE%" %PY_ARG% -m unittest discover -s "%ROOT%\tests"
goto WAIT_MENU
:BACKUP
"%PY_EXE%" %PY_ARG% -c "from core.database import DB_PATH,initialize; import sqlite3,datetime,pathlib; initialize(); d=pathlib.Path(DB_PATH).parent/'backups'; d.mkdir(exist_ok=True); target=d/('kyureika_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.sqlite3'); src=sqlite3.connect(DB_PATH); dst=sqlite3.connect(target); src.backup(dst); dst.close(); src.close(); print('Backup:',target)"
goto WAIT_MENU
:WAIT_MENU
echo.
pause
goto MENU

:PATH_ERROR
echo ERROR: Cannot access the launcher directory.
goto FAIL
:SITE_ERROR
echo ERROR: index.html not found next to Kyureika.bat.
goto FAIL
:FILE_ERROR
echo ERROR: main.py not found next to Kyureika.bat.
goto FAIL
:PY_ERROR
echo ERROR: Python 3.10 or newer is required.
echo Install from https://www.python.org/downloads/
goto FAIL
:INIT_ERROR
echo ERROR: SQLite initialization failed. Check folder permissions.
goto FAIL
:FAIL
echo.
pause
popd
endlocal
exit /b 1
:EXIT_OK
popd
endlocal
exit /b 0
