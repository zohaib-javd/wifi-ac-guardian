Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\Zohaib\Documents\WiFi_AC_Guardian_Windows\wifi-guardian-ui"
WshShell.Run """c:\Users\Zohaib\Documents\WiFi_AC_Guardian_Windows\wifi-guardian-ui\node_modules\electron\dist\electron.exe"" .", 0, False
