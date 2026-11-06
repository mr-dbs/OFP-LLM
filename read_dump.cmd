@echo off
rem read_dump.cmd (version 5) - 5 November: reads every .DMP in C:\ofp-llm\dump, one after the other, into
rem C:\ofp-llm\logs\dump_1.txt, dump_2.txt ... for Claude: which exe the dump came from (its full path and build
rem time), whether its symbols match, where the main thread was, and every thread's stack.
rem Version 5 no longer forces mismatched symbols: since the rebuild of 25 October they should match by themselves.
rem It reads no keyboard input, so it cannot hang waiting for you.
setlocal
set "CDB="
for %%p in ("C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe" "C:\Program Files\Windows Kits\10\Debuggers\x64\cdb.exe") do if exist %%p set "CDB=%%~p"
if not defined CDB for /f "delims=" %%p in ('where cdb.exe 2^>nul') do set "CDB=%%p"
if not defined CDB (echo cdb.exe was not found.& pause & goto :eof)
if not exist "C:\ofp-llm\dump\*.DMP" (echo No .DMP file in C:\ofp-llm\dump.& pause & goto :eof)
set "SYM=srv*C:\symbols*https://msdl.microsoft.com/download/symbols;C:\dev\CWR\build\win-x64-clang-rwdi\apps\cwr\Game;C:\dev\CWR\dist\x64-win-rwdi"
set "N=0"
for %%d in ("C:\ofp-llm\dump\*.DMP") do call :one "%%~fd"
echo.
echo Done: %N% dump(s) read. Tell Claude.
pause
goto :eof

:one
set /a N+=1
set "OUT=C:\ofp-llm\logs\dump_%N%.txt"
echo Reading %~nx1 ... a few minutes. If this window is still busy after 30 minutes, close it.
> "%OUT%" echo ===== dump file: %~f1  (saved %~t1, %~z1 bytes)
"%CDB%" -z "%~1" -y "%SYM%" -c ".reload /f;|;lmv m PoseidonGame*;.echo ===== main thread;~0s;kn 60;.echo ===== all threads;~*kb 30;q" < nul >> "%OUT%" 2>&1
for %%f in ("%OUT%") do echo    written %%~ff (%%~zf bytes)
goto :eof
