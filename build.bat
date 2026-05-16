@echo off
echo Building PS Cafe Manager...

if not exist .venv (
    echo Virtual environment not found. Run: python -m venv .venv
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt >nul 2>&1

echo Running PyInstaller...
pyinstaller --clean build.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful!
    echo Output: dist\PS-Cafe-Manager\
) else (
    echo.
    echo Build failed!
    exit /b 1
)
