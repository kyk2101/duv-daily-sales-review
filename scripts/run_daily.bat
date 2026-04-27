@echo off
chcp 65001 > nul 2>&1
setlocal EnableExtensions EnableDelayedExpansion

REM === DUV Sales Review - daily auto-update wrapper ===
REM Resolves repo root from this bat's parent dir.

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "VENV_PY=C:\Users\Admin\Desktop\DCSAI\.venv\Scripts\python.exe"
set "LOG_DIR=%REPO_ROOT%\logs"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" 2>nul

set "TS=%date:~0,4%%date:~5,2%%date:~8,2%"
set "LOG=%LOG_DIR%\run_%TS%.log"

call :LOG_LINE "===== START %date% %time% ====="
call :LOG_LINE "REPO_ROOT=%REPO_ROOT%"

if not exist "%VENV_PY%" (
    call :LOG_LINE "ERROR: venv python not found at %VENV_PY%"
    exit /b 10
)

cd /d "%REPO_ROOT%"
if errorlevel 1 (
    call :LOG_LINE "ERROR: cd to repo root failed"
    exit /b 11
)

set "PYTHONPATH=."

call :LOG_LINE "[1/4] fetch_data.py"
"%VENV_PY%" "src\service\sales_review_app\fetch_data.py" >> "%LOG%" 2>&1
if errorlevel 1 (
    call :LOG_LINE "ERROR: fetch failed exit=%errorlevel%"
    exit /b 20
)

call :LOG_LINE "[2/4] build_app.py"
"%VENV_PY%" "src\service\sales_review_app\build_app.py" >> "%LOG%" 2>&1
if errorlevel 1 (
    call :LOG_LINE "ERROR: build_app failed exit=%errorlevel%"
    exit /b 30
)

call :LOG_LINE "[3/4] build_html.py"
"%VENV_PY%" "src\service\sales_review_app\build_html.py" >> "%LOG%" 2>&1
if errorlevel 1 (
    call :LOG_LINE "ERROR: build_html failed exit=%errorlevel%"
    exit /b 40
)

call :LOG_LINE "[4/4] git push"
git add index.html "data/duv_review_data.json" >> "%LOG%" 2>&1
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "data: daily update %TS%" >> "%LOG%" 2>&1
    git push origin main >> "%LOG%" 2>&1
    if errorlevel 1 (
        call :LOG_LINE "ERROR: git push failed"
        exit /b 50
    )
    call :LOG_LINE "PUSHED"
) else (
    call :LOG_LINE "no changes to commit"
)

call :LOG_LINE "===== DONE %date% %time% ====="
endlocal
exit /b 0

:LOG_LINE
echo %~1
echo %~1 >> "%LOG%" 2>&1
exit /b 0
