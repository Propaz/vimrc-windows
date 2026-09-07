@echo off
REM Wrapper around vim-state-clean.py -- reports on Vim's undo/backup/swap dirs.
REM Reports only; pass --apply to actually delete. All arguments are forwarded.
REM
REM   vim-state-clean.bat                 report
REM   vim-state-clean.bat --apply         prune the safe categories
REM   vim-state-clean.bat --recover-cmds  list `vim -r` commands for risky swaps
setlocal

set "SCRIPT_DIR=%~dp0"
set "SCRIPT=%SCRIPT_DIR%vim-state-clean.py"

if not exist "%SCRIPT%" (
  echo Error: script not found: %SCRIPT%
  exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
  echo Error: python was not found on PATH.
  exit /b 1
)

python "%SCRIPT%" %*
exit /b %errorlevel%
