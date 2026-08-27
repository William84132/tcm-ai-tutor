@echo off
rem ============================================================
rem  Personal Data Backup
rem  Usage 1: double-click this file (backup to default folder)
rem  Usage 2: 个人数据备份.bat "D:\my-backup-folder"
rem  What it backs up: course notes, progress files, app data
rem  (users.db / .env / config.json) - see 使用说明.md
rem ============================================================
setlocal
echo ============================================================
echo  Personal Data Backup
echo ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0backup_data.ps1" %*
if errorlevel 1 (
  echo.
  echo [ERROR] Backup failed. Check the messages above.
) else (
  echo.
  echo [OK] Backup finished.
)
echo.
pause
