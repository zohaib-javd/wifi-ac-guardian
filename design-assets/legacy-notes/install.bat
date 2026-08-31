@echo off
TITLE WiFi AC Guardian Installer
echo ===================================================
echo   WiFi AC Guardian (Windows 11 Edition) Installer
echo ===================================================
echo.

python -m pip install .
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install Python package.
    pause
    exit /b %ERRORLEVEL%
)

echo Creating shortcuts...
python -c "from wifi_ac_guardian_win.config import sync_autostart_shortcut, sync_desktop_shortcut; sync_autostart_shortcut(True); sync_desktop_shortcut()"

echo.
echo [SUCCESS] WiFi AC Guardian installed successfully!
echo Opening Control Panel GUI...
start pythonw -m wifi_ac_guardian_win --gui
