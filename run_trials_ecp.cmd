@echo off
rem run_trials_ecp.cmd - nine-game trial with ECP and @new loaded after MFCTI (relay 25, run_trials 11).
rem Double-click it, or run it from a command prompt. Leave the window open; about three hours.
cd /d C:\ofp-llm
ollama stop gpt-oss:20b
python tests\run_tests.py > logs\tests_last.txt 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -File C:\ofp-llm\run_trials.ps1 -Only all -Rounds 3 -Matched -ExtraMods "@ECP;@new"
echo.
echo Trial finished. You can close this window.
pause
