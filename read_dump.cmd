@echo off
rem read_dump.cmd (version 4) - 25 October: reads where the game was stuck from C:\ofp-llm\PoseidonGame.DMP into
rem C:\ofp-llm\logs\dump_stacks4.txt, for Claude, with the game's own symbols. Version 3 fixes version 2, whose
rem debugger commands were garbled so that it waited for keyboard input for ever. It now reads no input at all.
setlocal
set "CDB="
for %%p in ("C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe" "C:\Program Files\Windows Kits\10\Debuggers\x64\cdb.exe") do if exist %%p set "CDB=%%~p"
if not defined CDB for /f "delims=" %%p in ('where cdb.exe 2^>nul') do set "CDB=%%p"
if not defined CDB (echo cdb.exe was not found.& pause & goto :eof)
if not exist "C:\ofp-llm\PoseidonGame.DMP" (echo C:\ofp-llm\PoseidonGame.DMP not found.& pause & goto :eof)
set "SYM=srv*C:\symbols*https://msdl.microsoft.com/download/symbols;C:\dev\CWR\build\win-x64-clang-rwdi\apps\cwr\Game;C:\dev\CWR\dist\x64-win-rwdi"
echo Reading the dump ... a few minutes at most. If this window is still busy after 30 minutes, close it.
"%CDB%" -z "C:\ofp-llm\PoseidonGame.DMP" -y "%SYM%" -c ".symopt+ 0x40;.reload /f /i PoseidonGame.exe;lmv m PoseidonGame;~0s;kn 60;.echo ===== all threads;~*kb 30;q" < nul > "C:\ofp-llm\logs\dump_stacks4.txt" 2>&1
for %%f in ("C:\dev\CWR\build\win-x64-clang-rwdi\apps\cwr\Game\PoseidonGame.pdb" "C:\dev\CWR\dist\x64-win-rwdi\PoseidonGame.exe") do echo FILE %%~tf %%~zf %%~ff>> "C:\ofp-llm\logs\dump_stacks4.txt" 2>&1
for %%f in ("C:\ofp-llm\logs\dump_stacks4.txt") do echo Written %%~ff (%%~zf bytes). Tell Claude.
pause
