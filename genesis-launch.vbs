' Genesis launcher: double-click = the dashboard opens in its own window, no
' terminal. A visible console appears ONLY for the first-run setup (it has
' real progress to show). Troubleshooting still has Genesis.bat.
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
    sh.Run """" & app & "\Genesis.bat""", 1, False
End If
