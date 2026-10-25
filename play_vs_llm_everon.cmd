@echo off
rem play_vs_llm_everon.cmd - play MFCTI on Everon as West against the LLM commander (East), with ECP and @new.
rem Both sides get the same funds: 200000 a side and 50000 a team (change the numbers on the "echo llmTestStart" line).
rem Opens the relay in its own window (leave it open), then starts the game. Close the relay window after the game.
rem The model gets 75 seconds a plan, because the game shares the graphics card with it while you play.
cd /d C:\ofp-llm
echo llmTestStart = []; llmTestFunds = [200000,50000]> "C:\Users\tumbl\Documents\Cold War Assault\MPMissions\mfcti116a_llmv1a.Eden\LLM\TestStart.sqf"
start "LLM relay - leave open" cmd /k python relay.py --deadline=75
timeout /t 3 /nobreak >nul
start "" "C:\dev\CWR\dist\x64-win-rwdi\PoseidonGame.exe" -C "E:\steam\steamapps\common\ARMA Cold War Assault\Remastered" --mod "C:\Users\tumbl\Documents\Cold War Assault\Workshop\@MFCTI;C:\Users\tumbl\Documents\Cold War Assault\Workshop\@ECP;C:\Users\tumbl\Documents\Cold War Assault\Workshop\@new"
echo.
echo Relay and game started. In the game: host "MFCTI 1.16a Coop Everon LLM", take the West commander slot.
echo Once you are in the mission, check the model here:
timeout /t 120 /nobreak
ollama ps
echo.
echo PROCESSOR must say 100%% GPU. If it shows CPU, the relay falls back to its rules.
pause
