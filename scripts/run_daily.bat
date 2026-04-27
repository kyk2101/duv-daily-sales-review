@echo off
REM ============================================================
REM DUV Sales Review - 매일 자동 갱신 + GitHub Push
REM 호출 위치: scripts/run_daily.bat
REM 작업 스케줄러: 매일 08:00 KST + 부팅 직후
REM ============================================================
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 > nul

REM 리포 루트로 이동 (이 스크립트의 부모 폴더)
set "REPO_ROOT=%~dp0.."
pushd "%REPO_ROOT%"

set "VENV_PY=C:\Users\Admin\Desktop\DCSAI\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo [run_daily] VENV not found at %VENV_PY%
  exit /b 1
)

set "LOG_DIR=%REPO_ROOT%\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\run_%date:~0,4%%date:~5,2%%date:~8,2%.log"

echo. >> "%LOG_FILE%"
echo ===== %date% %time% ===== >> "%LOG_FILE%"

REM 1. 데이터 fetch
echo [1/4] fetch >> "%LOG_FILE%"
set "PYTHONPATH=."
"%VENV_PY%" src\service\sales_review_app\fetch_data.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo [run_daily] fetch failed - aborting >> "%LOG_FILE%"
  popd
  exit /b 2
)

REM 2. JSON 빌드
echo [2/4] build_app >> "%LOG_FILE%"
"%VENV_PY%" src\service\sales_review_app\build_app.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo [run_daily] build_app failed >> "%LOG_FILE%"
  popd
  exit /b 3
)

REM 3. HTML 빌드
echo [3/4] build_html >> "%LOG_FILE%"
"%VENV_PY%" src\service\sales_review_app\build_html.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo [run_daily] build_html failed >> "%LOG_FILE%"
  popd
  exit /b 4
)

REM 4. Git push
echo [4/4] git push >> "%LOG_FILE%"
git add index.html data/duv_review_data.json >> "%LOG_FILE%" 2>&1
git diff --cached --quiet
if not errorlevel 1 (
  echo [run_daily] no changes to commit >> "%LOG_FILE%"
) else (
  for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value ^| findstr "="') do set "DT=%%I"
  set "TS=!DT:~0,8!-!DT:~8,4!"
  git commit -m "data: daily update !TS!" >> "%LOG_FILE%" 2>&1
  git push origin main >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    echo [run_daily] git push failed >> "%LOG_FILE%"
    popd
    exit /b 5
  )
  echo [run_daily] pushed >> "%LOG_FILE%"
)

echo [run_daily] DONE %date% %time% >> "%LOG_FILE%"
popd
exit /b 0
