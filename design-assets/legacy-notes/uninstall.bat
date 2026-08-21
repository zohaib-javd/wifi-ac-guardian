@echo off
TITLE WiFi AC Guardian Uninstaller
echo Uninstalling WiFi AC Guardian...
python -m pip uninstall -y wifi-ac-guardian-win
del "%USERPROFILE%\Desktop\WiFi AC Guardian.lnk" 2>nul
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\WiFi AC Guardian.lnk" 2>nul
echo Done.
pause
