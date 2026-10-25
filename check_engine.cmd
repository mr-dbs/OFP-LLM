@echo off
rem check_engine.cmd - 25 October: READ-ONLY. Records the state of the engine source in C:\dev\CWR (what git says
rem has changed, recent commits, branches) and the dates of the built game files, into
rem C:\ofp-llm\logs\engine_check.txt for Claude. It changes nothing.
setlocal
set "OUT=C:\ofp-llm\logs\engine_check.txt"
if not exist "C:\dev\CWR" (echo C:\dev\CWR not found.& pause & goto :eof)
cd /d C:\dev\CWR
> "%OUT%" echo ===== engine check %DATE% %TIME%
>>"%OUT%" echo ===== git branch and last commits
git branch -a >> "%OUT%" 2>&1
git log --oneline -20 --date=iso --format="%%h %%ad %%s" >> "%OUT%" 2>&1
>>"%OUT%" echo ===== git status (changed and new files not committed)
git status --short >> "%OUT%" 2>&1
>>"%OUT%" echo ===== git diff summary against the last commit
git diff --stat >> "%OUT%" 2>&1
>>"%OUT%" echo ===== git worktrees
git worktree list >> "%OUT%" 2>&1
>>"%OUT%" echo ===== files that mention the chat engine or the LLM bridge
findstr /s /m /i "SideChat llmRequest GameStateExtLlm" engine\*.cpp engine\*.h engine\*.hpp >> "%OUT%" 2>&1
>>"%OUT%" echo ===== built game files and their dates
for %%f in ("C:\dev\CWR\dist\x64-win-rwdi\PoseidonGame.exe" "C:\dev\CWR\dist\x64-win-rwdi\PoseidonServer.exe" "C:\dev\CWR\build\win-x64-clang-rwdi\apps\cwr\Game\PoseidonGame.exe" "C:\dev\CWR\build\win-x64-clang-rwdi\apps\cwr\Game\PoseidonGame.pdb") do if exist %%f (>>"%OUT%" echo %%~tf  %%~zf  %%~ff) else (>>"%OUT%" echo missing  %%~f)
>>"%OUT%" echo ===== other engine folders under C:\dev
dir /b /ad "C:\dev" >> "%OUT%" 2>&1
for %%f in ("%OUT%") do echo Written %%~ff (%%~zf bytes). Tell Claude.
pause
