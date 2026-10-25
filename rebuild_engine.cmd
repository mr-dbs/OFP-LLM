@echo off
rem rebuild_engine.cmd - 25 October. The matched rebuild: builds the game and server from the clean C:\dev\CWR
rem (branch llm, our changes only), so the exe and its debug files (PDB) come from one build.
rem   1. stops if the game or server is running, or C:\dev\CWR is not clean on branch llm
rem   2. backs up the current dist exe/pdb files to C:\ofp-llm\backup\dist_2026-10-25
rem   3. cmake --build build/win-x64-clang-rwdi  (full output: logs\build_output.txt)
rem   4. checks the new files' dates and that dist got the new exe; summary in logs\rebuild.txt
setlocal
set "CWR=C:\dev\CWR"
set "B=C:\dev\CWR\build\win-x64-clang-rwdi"
set "D=C:\dev\CWR\dist\x64-win-rwdi"
set "BK=C:\ofp-llm\backup\dist_2026-10-25"
set "LOG=C:\ofp-llm\logs\rebuild.txt"
set "OUT=C:\ofp-llm\logs\build_output.txt"
set "BAD="
cd /d "%CWR%" || goto stop
> "%LOG%" echo ===== matched rebuild, 25 October

echo Step 1 of 4: checks
tasklist /fi "imagename eq PoseidonGame.exe" | find /i "PoseidonGame.exe" >nul && set "BAD=1"
tasklist /fi "imagename eq PoseidonServer.exe" | find /i "PoseidonServer.exe" >nul && set "BAD=1"
if defined BAD echo The game or server is running. Close it and run this again.& goto stop
set "BR=none"
for /f %%b in ('git branch --show-current') do set "BR=%%b"
if not "%BR%"=="llm" echo C:\dev\CWR is on branch %BR%, not llm. Nothing done.& set "BAD=1"& goto stop
set "DIRTY="
for /f "delims=" %%l in ('git status --porcelain') do set "DIRTY=1"
if defined DIRTY echo C:\dev\CWR has uncommitted changes. Nothing done.& set "BAD=1"& goto stop
>>"%LOG%" echo step 1 ok: branch llm, nothing uncommitted, game and server closed
git log -1 --format="building from %%h %%s" >> "%LOG%"

echo Step 2 of 4: backing up the current dist files to %BK%
if not exist "%BK%" mkdir "%BK%"
for %%f in ("%D%\PoseidonGame.exe" "%D%\PoseidonServer.exe" "%D%\PoseidonGame.pdb" "%D%\PoseidonServer.pdb") do if exist %%f copy /y %%f "%BK%\" >nul
>>"%LOG%" echo ----- backed up (dates are the old files)
for %%f in ("%BK%\*.*") do >>"%LOG%" echo %%~tf  %%~zf  %%~nxf

echo Step 3 of 4: building. This can take a while; the window shows little until it ends...
cmake --build build/win-x64-clang-rwdi > "%OUT%" 2>&1
set "RC=%errorlevel%"
>>"%LOG%" echo build exit code: %RC%
if not "%RC%"=="0" echo The build FAILED. Your old game files are untouched in dist and backed up. Tell Claude.& set "BAD=1"& goto check

:check
echo Step 4 of 4: checking the new files
>>"%LOG%" echo ----- exe and pdb files now: build folder
for /r "%B%" %%f in (PoseidonGame.exe PoseidonGame.pdb PoseidonServer.exe PoseidonServer.pdb) do if exist "%%f" >>"%LOG%" echo %%~tf  %%~zf  %%f
>>"%LOG%" echo ----- dist folder
for %%f in ("%D%\*.exe" "%D%\*.pdb") do >>"%LOG%" echo %%~tf  %%~zf  %%~nxf
>>"%LOG%" echo ----- is the dist exe the one just built
for /r "%B%" %%f in (PoseidonGame.exe PoseidonServer.exe) do if exist "%%f" (fc /b "%%f" "%D%\%%~nxf" >nul && (>>"%LOG%" echo same: %%~nxf) || (>>"%LOG%" echo DIFFERENT: %%~nxf))
>>"%LOG%" echo ----- last 25 lines of the build output
powershell -NoProfile -Command "Get-Content -Tail 25 '%OUT%'" >> "%LOG%" 2>&1
echo.
if defined BAD (echo Finished with a problem. Tell Claude.) else (echo Done. Tell Claude.)

:stop
if defined BAD >>"%LOG%" echo stopped with a problem
pause
