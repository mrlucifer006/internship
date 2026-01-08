@echo off
echo Stopping Visitor Management System...
taskkill /F /IM "python.exe" /FI "WINDOWTITLE eq Visitor Management System*"
taskkill /F /IM "pythonw.exe"
echo Done.
pause
