@echo off
echo ===============================================
echo   Baseball Binder - Build Script
echo ===============================================
echo.

REM Clean previous builds
echo [1/3] Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo Done.
echo.

REM Build with PyInstaller
echo [2/3] Building executable with PyInstaller...
python -m PyInstaller BaseballBinder.spec --clean
if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)
echo Done.
echo.

REM Create release folder
echo [3/3] Creating release package...
if not exist "releases" mkdir "releases"

REM Get version from version.json
for /f "tokens=2 delims=:" %%a in ('findstr /r "\"version\"" version.json') do set VERSION=%%a
set VERSION=%VERSION: =%
set VERSION=%VERSION:"=%
set VERSION=%VERSION:,=%

REM Create timestamped release folder
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
set RELEASE_NAME=BaseballBinder-v%VERSION%-%mydate%

if not exist "releases\%RELEASE_NAME%" mkdir "releases\%RELEASE_NAME%"

REM Copy built files
xcopy "dist\BaseballBinder" "releases\%RELEASE_NAME%\" /E /I /Y
copy "README.md" "releases\%RELEASE_NAME%\" 2>nul

echo.
echo ===============================================
echo   Build Complete!
echo ===============================================
echo.
echo Executable location: releases\%RELEASE_NAME%\BaseballBinder.exe
echo.
echo To create an installer, you can use Inno Setup or similar tool.
echo.
pause
