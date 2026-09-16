; WiFi AC Guardian NSIS upgrade/uninstall process shutdown contract.
; The Electron window can be closed while guardian-backend.exe remains alive.
; Stop both process trees before NSIS touches the installed application files.

!macro CloseGuardianProcesses
  DetailPrint "Closing any running WiFi AC Guardian processes..."
  nsExec::ExecToLog 'taskkill /F /T /IM "WiFi AC Guardian.exe"'
  Pop $0
  nsExec::ExecToLog 'taskkill /F /T /IM "guardian-backend.exe"'
  Pop $0
  Sleep 1500
!macroend

!macro customInit
  !insertmacro CloseGuardianProcesses
!macroend

!macro customUnInit
  !insertmacro CloseGuardianProcesses
!macroend
