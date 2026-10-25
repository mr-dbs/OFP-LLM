@echo off
rem check_engine_diff.cmd - 25 October: READ-ONLY. Writes the full uncommitted changes of every changed engine file,
rem with each file's last-modified date, into C:\ofp-llm\logs\engine_diff.txt for Claude. It changes nothing.
setlocal
set "OUT=C:\ofp-llm\logs\engine_diff.txt"
cd /d C:\dev\CWR || (echo C:\dev\CWR not found.& pause & goto :eof)
> "%OUT%" echo ===== last-modified dates (the game you play was built 10/17/2026 11:46 PM)
for %%f in (engine\Poseidon\Game\Commands\GameStateExt.cpp engine\Poseidon\Game\Commands\GameStateExtLlm.cpp engine\Poseidon\Game\Commands\GameStateExtLlmDiag.cpp engine\Poseidon\Game\Commands\GameStateExtTestAudio.cpp engine\Poseidon\World\Entities\Infantry\SoldierOldAI.cpp engine\Poseidon\World\Entities\Infantry\SoldierOldActions.cpp engine\Poseidon\World\Entities\Vehicles\TransportCore.cpp engine\Poseidon\World\WorldImpl.cpp) do (>>"%OUT%" echo %%~tf  %%f)
>>"%OUT%" echo ===== full changes
git -c core.autocrlf=false diff >> "%OUT%" 2>&1
for %%f in ("%OUT%") do echo Written %%~ff (%%~zf bytes). Tell Claude.
pause
