@echo off
echo Installing PyInstaller...
python -m pip install pyinstaller

echo Building TimeFix.exe...
python -m PyInstaller --onefile --noconsole --name TimeFix src/timefix.py

if %errorlevel% neq 0 (
    echo Build failed!
    exit /b %errorlevel%
)

echo Build success!
echo Executable is in dist\TimeFix.exe
echo Done.
