@echo off
REM Create a symlink %USERPROFILE%\_vimrc -> <repo>\vim\_vimrc  (Windows only)
REM If a regular file already sits at the target, it is backed up first.
REM Requires Administrator rights OR Windows Developer Mode (for mklink).
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "SOURCE=%SCRIPT_DIR%vim\_vimrc"
set "TARGET=%USERPROFILE%\_vimrc"

if not exist "%SOURCE%" (
  echo Error: source file not found: %SOURCE%
  exit /b 1
)

if exist "%TARGET%" (
  dir "%TARGET%" 2>nul | findstr /C:"<SYMLINK>" >nul
  if !errorlevel! equ 0 (
    echo Removing existing symlink: %TARGET%
    del "%TARGET%"
  ) else (
    set "BACKUP=%TARGET%.backup"
    if exist "!BACKUP!" set "BACKUP=!BACKUP!.!RANDOM!"
    echo Backing up existing file: %TARGET% -^> !BACKUP!
    move /Y "%TARGET%" "!BACKUP!" >nul
  )
)

mklink "%TARGET%" "%SOURCE%"
if errorlevel 1 (
  echo.
  echo Failed to create symlink. Run this script as Administrator,
  echo or enable Windows Developer Mode, then run it again.
  exit /b 1
)
echo Done: %TARGET% -^> %SOURCE%
