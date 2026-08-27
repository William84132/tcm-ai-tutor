@echo off
rem ============================================================
rem  Migrate & Merge Personal Data
rem  Usage: drag your OLD project folder onto this file icon,
rem         or run: 迁移合并.bat "D:\old-project-folder"
rem
rem  It copies personal data (course notes, progress, app data)
rem  from the OLD folder into THIS folder. Nothing is ever
rem  deleted or overwritten - conflicts keep BOTH copies.
rem ============================================================
setlocal
if "%~1"=="" (
  echo [ERROR] No folder given.
  echo Please drag your OLD project folder onto this file,
  echo or run: 迁移合并.bat "D:\old-project-folder"
  echo.
  pause
  exit /b 1
)
echo ============================================================
echo  Migrate and Merge Personal Data
echo  Old folder : %~1
echo ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0merge_data.ps1" -OldRoot "%~1"
if errorlevel 1 (
  echo.
  echo [ERROR] Merge failed. Check the messages above.
) else (
  echo.
  echo [OK] Merge finished. Keep the old folder for a while.
)
echo.
pause
