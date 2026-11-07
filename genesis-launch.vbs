' Genesis launcher: double-click = the dashboard opens in its own window, no
' terminal, ever. On a machine where setup never ran, the first-run pipeline
' works hidden in the background (private Python/Node, deps, build) and the
' dashboard window opens by itself when ready. Troubleshooting: Genesis.bat.
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

app = fso.GetParentFolderName(WScript.ScriptFullName)
pw = ""
If fso.FileExists(app & "\backend\.venv\Scripts\pythonw.exe") Then
    pw = app & "\backend\.venv\Scripts\pythonw.exe"
ElseIf fso.FileExists(app & "\runtime\python\pythonw.exe") Then
    pw = app & "\runtime\python\pythonw.exe"
End If

If pw <> "" Then
    sh.CurrentDirectory = app
    sh.Run """" & pw & """ genesis.py up", 0, False
Else
    ' nothing installed yet: run the zero-touch first run, hidden
    sh.Run "powershell -NoProfile -ExecutionPolicy Bypass -File """ & app & "\scripts\first_run.ps1""", 0, False
End If
