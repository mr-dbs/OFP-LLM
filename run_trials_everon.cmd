@echo off
rem run_trials_everon.cmd - twelve-game trial on Everon with ECP and @new: stock, rules and model, four rounds,
rem fixed starts (Saint Phillippe against Durras and Le Moule against Laruns, each both ways round).
rem Install the Everon missions first (install_everon.cmd). Leave the window open; about four hours.
cd /d C:\ofp-llm
ollama stop gpt-oss:20b
python tests\run_tests.py > logs\tests_last.txt 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -File C:\ofp-llm\run_trials.ps1 -Island everon -Only all -Rounds 4 -Matched -ExtraMods "@ECP;@new"
echo.
echo Trial finished. You can close this window.
pause
