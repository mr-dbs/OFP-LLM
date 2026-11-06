@echo off
rem split_engine.cmd - 25 October. Separates the GR edits from this project's engine folder.
rem (version 2: checks no longer use findstr on git output)
rem   1. checks C:\dev\CWR is exactly as read this morning, else stops having changed nothing
rem   2. backs up every uncommitted change to C:\ofp-llm\backup\engine_2026-10-25
rem   3. makes C:\dev\CWR-gr: an exact copy of today's folder, GR edits included, for the GR project
rem   4. asks, then removes the GR edits from C:\dev\CWR
rem   5. commits our two changed files and the diag file on a new branch "llm"
rem   6. renames Bohemia's remote to "upstream" and switches off pushing to it
rem Nothing is deleted; nothing is pushed. Results in C:\ofp-llm\logs\engine_split.txt.
setlocal
set "CWR=C:\dev\CWR"
set "GR=C:\dev\CWR-gr"
set "LOG=C:\ofp-llm\logs\engine_split.txt"
set "BK=C:\ofp-llm\backup\engine_2026-10-25"
set "T=%TEMP%\cwrsplit"
set "F1=engine/Poseidon/Game/Commands/GameStateExt.cpp"
set "F2=engine/Poseidon/Game/Commands/GameStateExtTestAudio.cpp"
set "F3=engine/Poseidon/World/Entities/Infantry/SoldierOldAI.cpp"
set "F4=engine/Poseidon/World/Entities/Infantry/SoldierOldActions.cpp"
set "F5=engine/Poseidon/World/Entities/Vehicles/TransportCore.cpp"
set "F6=engine/Poseidon/World/WorldImpl.cpp"
set "F7=engine/Poseidon/Game/Commands/GameStateExtLlmDiag.cpp"
set "BAD="
cd /d "%CWR%" || goto stop
if exist "%GR%" echo %GR% already exists. Nothing done.& goto stop
if exist "%BK%" echo %BK% already exists. Nothing done.& goto stop
if exist "%T%" rmdir /s /q "%T%"
mkdir "%T%"
> "%LOG%" echo ===== engine split, 25 October

echo Step 1 of 6: checking C:\dev\CWR is as it was this morning...
set "HEADNOW=none"
for /f %%h in ('git rev-parse HEAD') do set "HEADNOW=%%h"
>>"%LOG%" echo last commit now: %HEADNOW%
>>"%LOG%" echo ----- changed and new files now
git status --porcelain --untracked-files=all >> "%LOG%" 2>&1
if /i not "%HEADNOW:~0,7%"=="ae9d139" echo The last commit is now %HEADNOW:~0,7%, not ae9d139. Nothing done.& goto stop
set "LIST= %F1% %F2% %F3% %F4% %F5% %F6% "
set "N=0"
for /f "delims=" %%f in ('git diff --name-only') do call :inlist "%%f"
if not "%N%"=="6" set "BAD=1"
set "LIST= %F7% "
set "N=0"
for /f "delims=" %%f in ('git ls-files --others --exclude-standard') do call :inlist "%%f"
if not "%N%"=="1" set "BAD=1"
if defined BAD echo The changed files are not the ones read this morning. Nothing done.& goto stop
>>"%LOG%" echo step 1 ok: HEAD ae9d139, the 6 changed files and the 1 new file as expected
echo.
echo This makes a backup and C:\dev\CWR-gr, then asks again before it removes anything from C:\dev\CWR.
choice /c YN /m "Go ahead"
if errorlevel 2 echo Stopped. Nothing done.& goto stop

echo Step 2 of 6: backup to %BK%
mkdir "%BK%"
git -c core.autocrlf=false diff > "%BK%\all_uncommitted.patch"
git -c core.autocrlf=false diff -- "%F2%" "%F3%" "%F4%" "%F6%" > "%BK%\gr_edits.patch"
for %%p in (%F1% %F2% %F3% %F4% %F5% %F6% %F7%) do call :copyone "%CWR%" "%BK%\files" "%%p"
if defined BAD echo A backup copy failed. Nothing removed.& goto stop
>>"%LOG%" echo step 2 ok: backup written to %BK%

echo Step 3 of 6: making %GR% - an exact copy for the GR project. This can take a few minutes...
git clone --no-hardlinks "%CWR%" "%GR%" >> "%LOG%" 2>&1 || (echo The copy failed. Nothing removed.& goto stop)
for %%p in (%F1% %F2% %F3% %F4% %F5% %F6% %F7%) do call :copyone "%CWR%" "%GR%" "%%p"
for %%p in (%F1% %F2% %F3% %F4% %F5% %F6% %F7%) do call :sameone "%CWR%" "%GR%" "%%p"
if defined BAD echo CWR-gr is not an exact copy. Nothing removed.& goto stop
git -C "%GR%" remote set-url origin https://github.com/BohemiaInteractive/CWR.git
git -C "%GR%" remote set-url --push origin DISABLED
>>"%LOG%" echo step 3 ok: %GR% holds all 7 files exactly as today; its pushing is switched off
>>"%LOG%" echo ----- CWR-gr status
git -C "%GR%" status --short >> "%LOG%" 2>&1
if exist "%CWR%\assets" >>"%LOG%" echo note: C:\dev\CWR\assets exists and was NOT copied - git does not track it
if exist "%CWR%\packages" >>"%LOG%" echo note: C:\dev\CWR\packages exists and was NOT copied - git does not track it

echo.
echo The GR edits are now safe in C:\dev\CWR-gr and in the backup.
choice /c YN /m "Remove the 4 GR edits from C:\dev\CWR now"
if errorlevel 2 echo Stopped. C:\dev\CWR unchanged.& goto stop

echo Step 4 of 6: removing the GR edits from C:\dev\CWR
git checkout -- "%F2%" "%F3%" "%F4%" "%F6%" >> "%LOG%" 2>&1
set "LIST= %F1% %F5% "
set "N=0"
for /f "delims=" %%f in ('git diff --name-only') do call :inlist "%%f"
if not "%N%"=="2" set "BAD=1"
if defined BAD echo Unexpected files left changed. Stopped before committing.& goto stop
>>"%LOG%" echo step 4 ok: only GameStateExt.cpp and TransportCore.cpp still changed

echo Step 5 of 6: committing our changes on branch llm
git switch -c llm >> "%LOG%" 2>&1 || (echo Could not make branch llm.& goto stop)
git add -- "%F1%" "%F5%" "%F7%"
git commit -q -m "Add LLM diag commands and the vehicle driver fix" -m "llmUnitInfo, llmGroupInfo and llmEngineInfo (GameStateExtLlmDiag.cpp); a driver who commands his own vehicle drops a move order left by a dead or dismounted commander (TransportCore.cpp)." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01Dih235KQhCZE5fghFNshou" >> "%LOG%" 2>&1 || (echo The commit failed.& goto stop)
git status --porcelain > "%T%\left.txt"
for %%f in ("%T%\left.txt") do if not "%%~zf"=="0" set "BAD=1"
if defined BAD echo Something is still uncommitted. See the log.& goto stop
>>"%LOG%" echo step 5 ok: committed on branch llm, nothing left uncommitted

echo Step 6 of 6: Bohemia's remote renamed to upstream, pushing to it switched off
git remote rename origin upstream >> "%LOG%" 2>&1
git remote set-url --push upstream DISABLED
>>"%LOG%" echo ----- remotes
git remote -v >> "%LOG%" 2>&1
>>"%LOG%" echo ----- our commits on top of Bohemia's 3.05
git log --format="%%h %%ad %%an : %%s" --date=short upstream/main..llm >> "%LOG%" 2>&1
>>"%LOG%" echo ----- every file that differs from Bohemia's 3.05
git diff --stat upstream/main..llm >> "%LOG%" 2>&1
git diff upstream/main..llm > "%T%\ours.diff"
findstr /i /c:"triGR" /c:"dbsPatrol" /c:"dbsGRLauncher" /c:"DBS GR" /c:"CreateMainOptions" "%T%\ours.diff" >nul && set "BAD=1"
if defined BAD (>>"%LOG%" echo CHECK FAILED: a GR marker is in our commits) else (>>"%LOG%" echo CHECK PASSED: no GR marker in our commits)
echo.
echo Done. Tell Claude.
goto stop

:inlist
rem counts a file that is in LIST; a file that is not in it is a problem
set "x=%~1"
call set "chk=%%LIST: %x% =%%"
if "%chk%"=="%LIST%" (set "BAD=1") else (set /a N+=1)
exit /b

:copyone
set "p=%~3"
set "p=%p:/=\%"
for %%d in ("%~2\%p%") do if not exist "%%~dpd" mkdir "%%~dpd"
copy /y "%~1\%p%" "%~2\%p%" >nul || set "BAD=1"
exit /b

:sameone
set "p=%~3"
set "p=%p:/=\%"
fc /b "%~1\%p%" "%~2\%p%" >nul || set "BAD=1"
exit /b

:stop
if defined BAD >>"%LOG%" echo stopped with a problem
pause
