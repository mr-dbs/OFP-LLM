@echo off
rem fix_freeze.cmd - 5 November: the engine fix for the freeze in heavy rocket and HE fire, then the rebuild.
rem   1. stops if THIS project's game or server (C:\dev\CWR\dist) is running; the GR test may keep running
rem   2. checks C:\dev\CWR is clean on branch llm
rem   3. applies apply_llm_nanfix.py (engine\Poseidon\World\Simulation\Collisions.cpp only), shows the change
rem   4. asks, then commits it on branch llm
rem   5. backs up the dist exe files, builds, and checks dist got the new exe
rem Log: C:\ofp-llm\logs\fix_freeze.txt   Build output: C:\ofp-llm\logs\build_output.txt
setlocal
set "CWR=C:\dev\CWR"
set "D=C:\dev\CWR\dist\x64-win-rwdi"
set "B=C:\dev\CWR\build\win-x64-clang-rwdi"
set "BK=C:\ofp-llm\backup\dist_2026-11-05"
set "LOG=C:\ofp-llm\logs\fix_freeze.txt"
set "BAD="
cd /d "%CWR%" || goto stop
> "%LOG%" echo ===== freeze fix, 5 November

echo Step 1 of 5: is this project's game or server running?
set "RUN=0"
for /f %%n in ('powershell -NoProfile -Command "(Get-Process PoseidonGame,PoseidonServer -ErrorAction SilentlyContinue | Where-Object { $_.Path -like 'C:\dev\CWR\dist\*' }).Count"') do set "RUN=%%n"
if not "%RUN%"=="0" echo This project's game or server is running. Close it, then run this again.& set "BAD=1"& goto stop

echo Step 2 of 5: checking C:\dev\CWR
set "BR=none"
for /f %%b in ('git branch --show-current') do set "BR=%%b"
if not "%BR%"=="llm" echo C:\dev\CWR is on branch %BR%, not llm. Nothing done.& set "BAD=1"& goto stop
set "DIRTY="
for /f "delims=" %%l in ('git status --porcelain') do set "DIRTY=1"
if defined DIRTY echo C:\dev\CWR has uncommitted changes. Nothing done.& set "BAD=1"& goto stop

echo Step 3 of 5: applying the fix
python C:\ofp-llm\apply_llm_nanfix.py "%CWR%" >> "%LOG%" 2>&1 || (echo The fix could not be applied. See the log.& set "BAD=1"& goto stop)
git --no-pager diff --stat
git -c core.autocrlf=false diff >> "%LOG%" 2>&1
set "N=0"
for /f "delims=" %%l in ('git diff --name-only') do set /a N+=1
if not "%N%"=="1" echo Expected exactly one changed file. Nothing committed.& set "BAD=1"& goto stop
echo.
choice /c YN /m "Commit this fix on branch llm and rebuild"
if errorlevel 2 echo Stopped. The change is applied but not committed. Tell Claude.& goto stop

echo Step 4 of 5: committing
git add -- engine/Poseidon/World/Simulation/Collisions.cpp
git commit -q -m "Skip explosions at a non-finite position (freeze fix)" -m "A shell exploding at a NaN position made Landscape::Visible walk about 2.1 billion map cells per nearby object, freezing the game with its sound looping (dumps of 24 Oct and 5 Nov 2026). Guards in ExplosionDammage, ExplosionDammageEffects and Visible; no change for finite values." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01Dih235KQhCZE5fghFNshou" >> "%LOG%" 2>&1 || (echo The commit failed. See the log.& set "BAD=1"& goto stop)
git log -1 --format="committed %%h %%s" >> "%LOG%"

echo Step 5 of 5: backing up and building. A few minutes; the window stays quiet until it ends...
if not exist "%BK%" mkdir "%BK%"
for %%f in ("%D%\PoseidonGame.exe" "%D%\PoseidonServer.exe" "%D%\PoseidonGame.pdb" "%D%\PoseidonServer.pdb") do if exist %%f copy /y %%f "%BK%\" >nul
cmake --build build/win-x64-clang-rwdi > "C:\ofp-llm\logs\build_output.txt" 2>&1
set "RC=%errorlevel%"
>>"%LOG%" echo build exit code: %RC%
if not "%RC%"=="0" echo The build FAILED. Your old game files are untouched and backed up. Tell Claude.& set "BAD=1"& goto stop
>>"%LOG%" echo ----- is the dist exe the one just built
for /r "%B%" %%f in (PoseidonGame.exe PoseidonServer.exe) do if exist "%%f" (fc /b "%%f" "%D%\%%~nxf" >nul && (>>"%LOG%" echo same: %%~nxf %%~tf) || (>>"%LOG%" echo DIFFERENT: %%~nxf& set "BAD=1"))
echo.
if defined BAD (echo Finished with a problem. Tell Claude.) else (echo Done. Tell Claude.)

:stop
if defined BAD >>"%LOG%" echo stopped with a problem
pause
