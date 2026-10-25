@echo off
rem backup_to_github.cmd - 25 October. Backs up this project to two PRIVATE GitHub repos you made empty.
rem   Mod:    C:\ofp-llm - relay, tools, tests, launchers, engine patch scripts, and a copy of the four
rem           installed missions (missions\). Left out: the dump, logs, backups, old pack folders, zips, rars.
rem   Engine: C:\dev\CWR branch llm - Bohemia's public 3.05 plus our two commits (checked clean of GR edits).
rem It shows you every file and asks before each push. GitHub may open a browser window to sign you in.
rem Run it again any time later: it commits what changed and pushes again. Log: C:\ofp-llm\logs\github.txt
setlocal
set "MOD=C:\ofp-llm"
set "CWR=C:\dev\CWR"
set "MIS=C:\Users\tumbl\Documents\Cold War Assault\Missions"
set "LOG=C:\ofp-llm\logs\github.txt"
set "BAD="
> "%LOG%" echo ===== GitHub backup %DATE% %TIME%

rem ---------- the two repo addresses: asked the first time, remembered after
set "MODURL="
set "ENGURL="
for /f "delims=" %%u in ('git -C "%MOD%" remote get-url origin 2^>nul') do set "MODURL=%%u"
for /f "delims=" %%u in ('git -C "%CWR%" remote get-url origin 2^>nul') do set "ENGURL=%%u"
if not defined MODURL set /p "MODURL=Paste the address of the empty private repo for the MOD (C:\ofp-llm): "
if not defined ENGURL set /p "ENGURL=Paste the address of the empty private repo for the ENGINE (C:\dev\CWR): "
call :checkurl "%MODURL%"
call :checkurl "%ENGURL%"
if /i "%MODURL%"=="%ENGURL%" set "BAD=1"
if defined BAD echo Those addresses are not right: each must start https://github.com/, be different, and not be Bohemia's. Nothing done.& goto stop
>>"%LOG%" echo mod repo:    %MODURL%
>>"%LOG%" echo engine repo: %ENGURL%

rem ---------- who the commits are by: the same name and e-mail as the engine's commits
set "GN="
set "GE="
for /f "delims=" %%n in ('git -C "%CWR%" config user.name') do set "GN=%%n"
for /f "delims=" %%n in ('git -C "%CWR%" config user.email') do set "GE=%%n"

echo.
echo ===== MOD: C:\ofp-llm
echo Copying the four installed missions into C:\ofp-llm\missions ...
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe mfcti116a_llmv1a.Eden mfcti116a_stock.Eden) do call :mission %%m
if defined BAD echo A mission copy failed. Nothing committed.& goto stop
cd /d "%MOD%" || goto stop
if not exist ".git" git init -q -b main >> "%LOG%" 2>&1
if defined GN git config user.name "%GN%"
if defined GE git config user.email "%GE%"
> .gitignore echo # Left out of the GitHub backup
>>.gitignore echo *.DMP
>>.gitignore echo *.dmp
>>.gitignore echo logs/
>>.gitignore echo backup/
>>.gitignore echo pack*/
>>.gitignore echo __pycache__/
>>.gitignore echo *.pyc
>>.gitignore echo *.zip
>>.gitignore echo *.rar
git add -A
>>"%LOG%" echo ----- mod files to commit
git status --short >> "%LOG%" 2>&1
set "N=0"
for /f "delims=" %%l in ('git status --short') do set /a N+=1
echo.
git status --short
echo.
echo %N% changed files above. The full list is also in logs\github.txt.
if "%N%"=="0" echo Nothing new in the mod since the last backup.& goto modpush
choice /c YN /m "Commit these to the MOD repo"
if errorlevel 2 echo Stopped. Nothing committed.& goto stop
git commit -q -m "Backup %DATE%" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01Dih235KQhCZE5fghFNshou" >> "%LOG%" 2>&1 || (echo The commit failed. See the log.& set "BAD=1"& goto stop)

:modpush
git remote get-url origin >nul 2>&1 || git remote add origin "%MODURL%"
choice /c YN /m "Push the MOD to %MODURL%"
if errorlevel 2 echo Mod not pushed.& goto engine
git push -u origin main >> "%LOG%" 2>&1 && (echo MOD pushed.& >>"%LOG%" echo MOD pushed) || (echo MOD PUSH FAILED. See logs\github.txt.& >>"%LOG%" echo MOD PUSH FAILED& set "BAD=1")

:engine
echo.
echo ===== ENGINE: C:\dev\CWR branch llm
cd /d "%CWR%" || goto stop
set "BR=none"
for /f %%b in ('git branch --show-current') do set "BR=%%b"
if not "%BR%"=="llm" echo C:\dev\CWR is on %BR%, not llm. Engine not pushed.& set "BAD=1"& goto stop
set "DIRTY="
for /f "delims=" %%l in ('git status --porcelain') do set "DIRTY=1"
if defined DIRTY echo C:\dev\CWR has uncommitted changes. Engine not pushed - tell Claude.& set "BAD=1"& goto stop
git diff upstream/main..llm > "%TEMP%\ours.diff"
findstr /i /c:"triGR" /c:"dbsPatrol" /c:"dbsGRLauncher" /c:"DBS GR" "%TEMP%\ours.diff" >nul && (echo A GR marker is in our commits. Engine not pushed - tell Claude.& set "BAD=1"& goto stop)
>>"%LOG%" echo ----- engine: our commits and every file that differs from Bohemia's 3.05
git log --format="%%h %%ad %%an : %%s" --date=short upstream/main..llm >> "%LOG%" 2>&1
git diff --stat upstream/main..llm >> "%LOG%" 2>&1
echo Our commits on top of Bohemia's 3.05, and the files they change:
git log --format="  %%h %%s" upstream/main..llm
git diff --stat upstream/main..llm
echo No GR marker found. The push also carries Bohemia's public history, so the first one can take a while.
git remote get-url origin >nul 2>&1 || git remote add origin "%ENGURL%"
choice /c YN /m "Push the ENGINE to %ENGURL%"
if errorlevel 2 echo Engine not pushed.& goto stop
git push -u origin llm >> "%LOG%" 2>&1 && (echo ENGINE pushed.& >>"%LOG%" echo ENGINE pushed) || (echo ENGINE PUSH FAILED. See logs\github.txt.& >>"%LOG%" echo ENGINE PUSH FAILED& set "BAD=1")
goto stop

:checkurl
echo %~1| findstr /b /i /c:"https://github.com/" >nul || set "BAD=1"
echo %~1| findstr /i /c:"BohemiaInteractive" >nul && set "BAD=1"
exit /b

:mission
if not exist "%MIS%\%1\LLM\Report.sqs" echo MISSING: %MIS%\%1& set "BAD=1"& exit /b
robocopy "%MIS%\%1" "%MOD%\missions\%1" /MIR /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 set "BAD=1"
echo   copied %1
exit /b

:stop
echo.
if defined BAD (echo Finished with a problem. Tell Claude.) else (echo Done. Tell Claude.)
pause
