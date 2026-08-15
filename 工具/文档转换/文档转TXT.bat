@echo off
rem ============================================================
rem  Doc2TXT v1.0 - local PDF/DOCX/DOC to TXT converter
rem  Usage: drag PDF/DOCX/DOC files or folders onto this file
rem  Output: 转换输出\ subfolder next to each source file
rem ============================================================
setlocal
if "%~1"=="" (
  echo No file or folder given.
  echo Drag PDF/DOCX/DOC files or folders onto this file icon.
  echo.
  pause
  exit /b 1
)
python "%~dp0文档转TXT.py" %*
echo.
pause
