@echo off
rem cleanup.cmd - 5 November: tidies C:\ofp-llm. It MOVES, it deletes nothing.
rem   to C:\ofp-llm\archive : old installers (packs 26-34, Everon), old pack folders 26-34, one-off scripts, OFP-LLM.rar
rem   to C:\ofp-llm\logs\archive : every log, trial zip and manifest dated before 22 October, old dump readings
rem Then it offers to run backup_to_github.cmd. Log: C:\ofp-llm\logs\cleanup.txt
setlocal
set "R=C:\ofp-llm"
set "A=C:\ofp-llm\archive"
set "LOG=C:\ofp-llm\logs\cleanup.txt"
set "FILES=install_pack26.cmd install_pack27.cmd install_pack28.cmd install_pack29.cmd install_pack31.cmd install_pack32.cmd install_pack33.cmd install_pack34.cmd install_everon.cmd check_engine.cmd check_engine_diff.cmd check_git_history.cmd split_engine.cmd read_dump_locals.cmd fix_freeze.cmd fix_freeze_gr.cmd OFP-LLM.rar"
set "DIRS=pack26 pack27 pack28 pack29 pack30 pack31 pack32 pack33 pack34"
cd /d "%R%" || goto :eof
netstat -ano | findstr ":8777" | findstr "LISTENING" >nul && (echo A relay is running. Close the game and the relay first.& pause & goto :eof)

echo These go to C:\ofp-llm\archive:
for %%f in (%FILES%) do if exist "%%f" echo    %%f
for %%d in (%DIRS%) do if exist "%%d\" echo    %%d\
set "OLD=0"
for /f %%n in ('powershell -NoProfile -Command "(Get-ChildItem C:\ofp-llm\logs -File | Where-Object { ($_.Name -match '_(2026\d{4})_' -and [int]$Matches[1] -lt 20261022) -or $_.Name -eq 'server.log' -or $_.Name -like 'dump_stacks*' }).Count"') do set "OLD=%%n"
echo And %OLD% old log files go to C:\ofp-llm\logs\archive.
echo Staying on top: the relay, launchers, trial scripts, install_pack35, rebuild_engine, read_dump, the apply scripts,
echo backup_to_github, sync_mpmissions, tests, tools, missions, backup, and the recent logs.
echo.
choice /c YN /m "Move them"
if errorlevel 2 echo Nothing moved.& pause & goto :eof

> "%LOG%" echo ===== cleanup %DATE% %TIME%
if not exist "%A%" mkdir "%A%"
for %%f in (%FILES%) do if exist "%%f" move /y "%%f" "%A%\" >nul && (>>"%LOG%" echo moved %%f)
for %%d in (%DIRS%) do if exist "%%d\" move "%%d" "%A%\" >nul && (>>"%LOG%" echo moved %%d\)
if not exist "%R%\logs\archive" mkdir "%R%\logs\archive"
powershell -NoProfile -Command "Get-ChildItem C:\ofp-llm\logs -File | Where-Object { ($_.Name -match '_(2026\d{4})_' -and [int]$Matches[1] -lt 20261022) -or $_.Name -eq 'server.log' -or $_.Name -like 'dump_stacks*' } | Move-Item -Destination C:\ofp-llm\logs\archive -PassThru | Measure-Object | ForEach-Object { 'moved ' + $_.Count + ' log files to logs\archive' }" >> "%LOG%" 2>&1
type "%LOG%"
echo.
echo Not touched: C:\ofp-llm\dump (about 10 GB). Delete those two dumps yourself when you no longer need them.
echo.
choice /c YN /m "Run the GitHub backup now"
if errorlevel 2 echo OK. Run backup_to_github.cmd later.& pause & goto :eof
call "%R%\backup_to_github.cmd"
