@echo off
rem run_test_guard_everon.cmd - four headless games on Everon with ECP and @new: rules and model, two rounds.
rem Round 1 starts East at Saint Phillippe, round 2 at Durras, next to a resistance town. In every game the relay
rem makes up an attacker 800 m from East's base at game minute 20. About 80 minutes. Run install_pack31.cmd first.
cd /d C:\ofp-llm
ollama stop gpt-oss:20b
powershell -NoProfile -ExecutionPolicy Bypass -File C:\ofp-llm\run_trials.ps1 -Island everon -Only control -Rounds 2 -Matched -ExtraMods "@ECP;@new" -RelayOptions "--test-threat=20"
echo.
echo Test finished. You can close this window.
pause
