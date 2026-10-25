@echo off
rem run_trials_head_everon.cmd - the model against the rules, on Everon with ECP and @new, equal funds for both
rem sides (200000 a side, 50000 a team). Each round plays twice: the model on East, then the model on West, from
rem the same start. Four rounds, eight games, about 2 hours 45 minutes. Run install_pack32.cmd first.
cd /d C:\ofp-llm
ollama stop gpt-oss:20b
python tests\run_tests.py > logs\tests_last.txt 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -File C:\ofp-llm\run_trials.ps1 -Island everon -Only head -Rounds 4 -Matched -ExtraMods "@ECP;@new" -Funds "200000,50000"
echo.
echo Trial finished. You can close this window.
pause
