' Zero-touch first run: the installer (or the Start-menu shortcut on a machine
' with no Python yet) fires this hidden and detached. It needs nothing on the
' machine - no console window exists to close, no keys to press. Genesis
' prepares itself completely in the background and the dashboard window opens
' by itself when everything is ready. Progress: logs\first-run.log.
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

app = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = app

' window style 0 = hidden, False = fire-and-forget (installer exits instantly)
sh.Run "powershell -NoProfile -ExecutionPolicy Bypass -File """ & app & "\scripts\first_run.ps1""", 0, False
