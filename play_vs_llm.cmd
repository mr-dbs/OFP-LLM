@echo off
rem play_vs_llm.cmd - play MFCTI as West against the LLM commander (East), with ECP and @new.
rem Opens the relay in its own window (leave it open), then starts the game. Close the relay window after the game.
cd /d C:\ofp-llm
start "LLM relay - leave open" cmd /k python relay.py
timeout /t 3 /nobreak >nul
start "" "C:\dev\CWR\dist\x64-win-rwdi\PoseidonGame.exe" -C "E:\steam\steamapps\common\ARMA Cold War Assault\Remastered" --mod "C:\Users\tumbl\Documents\Cold War Assault\Workshop\@MFCTI;C:\Users\tumbl\Documents\Cold War Assault\Workshop\@ECP;C:\Users\tumbl\Documents\Cold War Assault\Workshop\@new"
echo.
echo Relay and game started. In the game: host mfcti116a_llmv1a, take the West commander slot.
echo Once you are in the mission, check the model here:
timeout /t 120 /nobreak
ollama ps
echo.
echo PROCESSOR must say 100%% GPU. If it shows CPU, the relay falls back to its rules.
pause
