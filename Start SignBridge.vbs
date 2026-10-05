Option Explicit

Dim shell, files, projectFolder, pythonWindow, applicationFile, command
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")

projectFolder = files.GetParentFolderName(WScript.ScriptFullName)
pythonWindow = files.BuildPath(projectFolder, ".venv\Scripts\pythonw.exe")
applicationFile = files.BuildPath(projectFolder, "app.py")

If Not files.FileExists(pythonWindow) Then
    MsgBox "SignBridge needs its one-time setup first." & vbCrLf & vbCrLf & _
        "Right-click setup.ps1, choose Run with PowerShell, and let it finish.", _
        vbExclamation, "SignBridge UAE"
    WScript.Quit 1
End If

shell.CurrentDirectory = projectFolder
command = Chr(34) & pythonWindow & Chr(34) & " " & Chr(34) & applicationFile & Chr(34)
shell.Run command, 0, False
