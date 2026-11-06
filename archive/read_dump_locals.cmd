@echo off
rem read_dump_locals.cmd - 5 November: READ-ONLY. From your game's dump of tonight, the values inside the two stuck
rem functions (Landscape::Visible and Landscape::ExplosionDammage): the explosion's position, the object's, and the
rem loop counters. Writes C:\ofp-llm\logs\dump_locals.txt for Claude. It reads no keyboard input.
setlocal
set "D=C:\ofp-llm\dump\PoseidonGame (2).DMP"
set "CDB="
for %%p in ("C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe" "C:\Program Files\Windows Kits\10\Debuggers\x64\cdb.exe") do if exist %%p set "CDB=%%~p"
if not defined CDB for /f "delims=" %%p in ('where cdb.exe 2^>nul') do set "CDB=%%p"
if not defined CDB (echo cdb.exe was not found.& pause & goto :eof)
if not exist "%D%" goto nodump
set "SYM=srv*C:\symbols*https://msdl.microsoft.com/download/symbols;C:\dev\CWR\build\win-x64-clang-rwdi\apps\cwr\Game;C:\dev\CWR\dist\x64-win-rwdi"
echo Reading the dump ... a few minutes.
"%CDB%" -z "%D%" -y "%SYM%" -c ".reload /f PoseidonGame.exe;~0s;.echo ===== frame 0 Visible;.frame 0;dv /t /v;.echo ===== frame 0 from;dt -r1 from;.echo ===== frame 0 to;dt -r1 to;.echo ===== frame 1 ExplosionDammage;.frame 1;dv /t /v;.echo ===== frame 1 pos;dt -r1 pos;.echo ===== frame 2 ShotShell;.frame 2;dv /t /v;q" < nul > "C:\ofp-llm\logs\dump_locals.txt" 2>&1
for %%f in ("C:\ofp-llm\logs\dump_locals.txt") do echo Written %%~ff (%%~zf bytes). Tell Claude.
pause
goto :eof

:nodump
echo The dump of your game was not found in C:\ofp-llm\dump.
pause
