@echo off
setlocal enabledelayedexpansion

set "deployment_location=K:\10. Released Software\Systems Manufacturing Support\Manual Rotary and Angular"
set "local_git_repository=C:\Users\tbates\Python\manual-rotary-and-angular"
set "repository_name=Manual Rotary and Angular"

set "filelist=AerotechDataCal.py AerotechPDF.py AngularTest.py MetrologyTestInterface.py RotaryCalTest.py changelog.md README.md plot_manager.py"

echo This script will overwrite all files in %deployment_location%
pause

if not exist "%deployment_location%" mkdir "%deployment_location%"

For /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set "mydate=%%c-%%a-%%b")
For /f "tokens=1-2 delims=/:" %%a in ("%TIME%") do (set "mytime=%%a-%%b")

echo %username% released an update for %repository_name% at %TIME% on %DATE% >> "%deployment_location%\ReleaseLog.txt"
echo.  >> "%deployment_location%\ReleaseLog.txt"

echo Latest Commit: >> "%deployment_location%\ReleaseLog.txt"
git log -1 >> "%deployment_location%\ReleaseLog.txt"
echo.  >> "%deployment_location%\ReleaseLog.txt"

echo Tag: >> "%deployment_location%\ReleaseLog.txt"
git tag --points-at HEAD >> "%deployment_location%\ReleaseLog.txt"
echo.  >> "%deployment_location%\ReleaseLog.txt"

echo --------------------------------------------------------------------------- >> "%deployment_location%\ReleaseLog.txt"
echo.  >> "%deployment_location%\ReleaseLog.txt"

attrib +H "%deployment_location%\ReleaseLog.txt"

for %%F in (%filelist%) do (
    echo f | xcopy /y "%local_git_repository%\%%F" "%deployment_location%\%%F"
    echo "%local_git_repository%\%%F"
    echo "%deployment_location%\%%F"
)

pause
