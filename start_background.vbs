Set WshShell = CreateObject("WScript.Shell")
' Use 'py -w' to run with the python windowless launcher
WshShell.Run "py -w run.py", 0
Set WshShell = Nothing
