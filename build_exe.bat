@echo off
setlocal
cd /d "%~dp0"
echo ========================================
echo PayrollPro - Windows EXE Builder
echo ========================================
echo.
python -m pip install --upgrade pyinstaller
if errorlevel 1 (
  echo Failed to install/update PyInstaller.
  pause
  exit /b 1
)
python -m PyInstaller --noconfirm --clean --onefile --windowed --name PayrollPro app.py
if exist "dist\PayrollPro.exe" (
  echo.
  echo BUILD COMPLETE!
  echo EXE: %CD%\dist\PayrollPro.exe
) else (
  echo.
  echo BUILD FAILED.
)
pause
