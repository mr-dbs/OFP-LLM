@echo off
rem fix_freeze_gr.cmd - 5 November: the same freeze fix for the GR project's engine copy, C:\dev\CWR-gr.
rem   1. stops if the GR game or server (C:\dev\CWR-gr\dist) is running
rem   2. backs up its Collisions.cpp and dist exe files to C:\ofp-llm\backup\gr_2026-11-05
rem   3. applies apply_llm_nanfix.py to C:\dev\CWR-gr (Collisions.cpp only) and shows the change
rem   4. asks, then builds C:\dev\CWR-gr and checks its dist got the new exe
rem It does NOT commit anything in C:\dev\CWR-gr: that folder's git is the GR project's to manage.
rem Log: C:\ofp-llm\logs\fix_freeze_gr.txt   Build output: C:\ofp-llm\logs\build_output_gr.txt
setlocal
set "GR=C:\dev\CWR-gr"
set "F=engine\Poseidon\World\Simulation\Collisions.cpp"
set "D=C:\dev\CWR-gr\dist\x64-win-rwdi"
set "B=C:\dev\CWR-gr\build\win-x64-clang-rwdi"
set "BK=C:\ofp-llm\backup\gr_2026-11-05"
set "LOG=C:\ofp-llm\logs\fix_freeze_gr.txt"
set "BAD="
cd /d "%GR%" || goto stop
if not exist "%B%" echo %B% not found: the GR copy has not been built yet. Nothing done.& set "BAD=1"& goto stop
> "%LOG%" echo ===== freeze fix for CWR-gr, 5 November

echo Step 1 of 4: is the GR game or server running?
set "RUN=0"
for /f %%n in ('powershell -NoProfile -Command "(Get-Process PoseidonGame,PoseidonServer -ErrorAction SilentlyContinue | Where-Object { $_.Path -like 'C:\dev\CWR-gr\dist\*' }).Count"') do set "RUN=%%n"
if not "%RUN%"=="0" echo The GR game or server is running. Close it, then run this again.& set "BAD=1"& goto stop

echo Step 2 of 4: backing up to %BK%
if not exist "%BK%" mkdir "%BK%"
copy /y "%GR%\%F%" "%BK%\Collisions.cpp" >nul || (echo Backup failed. Nothing done.& set "BAD=1"& goto stop)
for %%f in ("%D%\PoseidonGame.exe" "%D%\PoseidonServer.exe" "%D%\PoseidonGame.pdb" "%D%\PoseidonServer.pdb") do if exist %%f copy /y %%f "%BK%\" >nul

echo Step 3 of 4: applying the fix
python C:\ofp-llm\apply_llm_nanfix.py "%GR%" >> "%LOG%" 2>&1 || (echo The fix could not be applied. Nothing changed. See the log.& set "BAD=1"& goto stop)
type "%LOG%"
fc "%BK%\Collisions.cpp" "%GR%\%F%" >> "%LOG%" 2>&1
echo.
choice /c YN /m "Build the GR copy with the fix now"
if errorlevel 2 echo Stopped. The fix is in the GR source but not built. The original is in %BK%.& goto stop

echo Step 4 of 4: building. A few minutes; the window stays quiet until it ends...
cmake --build build/win-x64-clang-rwdi > "C:\ofp-llm\logs\build_output_gr.txt" 2>&1
set "RC=%errorlevel%"
>>"%LOG%" echo build exit code: %RC%
if not "%RC%"=="0" echo The build FAILED. The old GR exe files are untouched and backed up. Tell Claude.& set "BAD=1"& goto stop
>>"%LOG%" echo ----- is the dist exe the one just built
for /r "%B%" %%f in (PoseidonGame.exe PoseidonServer.exe) do if exist "%%f" if exist "%D%\%%~nxf" (fc /b "%%f" "%D%\%%~nxf" >nul && (>>"%LOG%" echo same: %%~nxf %%~tf) || (>>"%LOG%" echo DIFFERENT: %%~nxf& set "BAD=1"))
echo.
if defined BAD (echo Finished with a problem. Tell Claude.) else (echo Done. Tell Claude.)

:stop
if defined BAD >>"%LOG%" echo stopped with a problem
pause
