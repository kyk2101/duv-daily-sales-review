# Windows 작업 스케줄러 등록 - DUV Sales Review 매일 갱신
# 실행: 관리자 PowerShell에서 ./setup_scheduler.ps1
#   - 매일 08:00 KST + 부팅 직후 (예약 시간 놓치면 즉시 catch-up)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BatPath = Join-Path $RepoRoot 'scripts\run_daily.bat'

if (-not (Test-Path $BatPath)) {
    Write-Error "run_daily.bat not found at $BatPath"
    exit 1
}

$TaskName = 'DUV_Sales_Review_Daily'

# 기존 태스크 제거 (있는 경우)
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

$Action = New-ScheduledTaskAction -Execute $BatPath -WorkingDirectory $RepoRoot

$Trigger1 = New-ScheduledTaskTrigger -Daily -At 8:00am
$Trigger2 = New-ScheduledTaskTrigger -AtLogOn

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -MultipleInstances IgnoreNew

$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger @($Trigger1, $Trigger2) `
    -Settings $Settings `
    -Principal $Principal `
    -Description 'DUVETICA Sales Review: 매일 08:00 + 로그온 시 자동 갱신 후 GitHub push'

Write-Host "OK Registered task: $TaskName"
Write-Host "  - Daily 08:00 KST"
Write-Host "  - At logon"
Write-Host "  - Run task as soon as possible after a scheduled start is missed: ENABLED"
Write-Host ""
Write-Host "테스트 실행: Start-ScheduledTask -TaskName $TaskName"
Write-Host "수동 삭제:   Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"
