@echo off
rem run_test_basedefence.cmd - two headless games (rules and model, round 1) with ECP and @new, in which the relay
rem makes up an attacker 800 m from East's base at game minute 20. About 45 minutes. Install the pack first.
cd /d C:\ofp-llm
ollama stop gpt-oss:20b
powershell -NoProfile -ExecutionPolicy Bypass -File C:\ofp-llm\run_trials.ps1 -Only control -Rounds 1 -Matched -ExtraMods "@ECP;@new" -RelayOptions "--test-threat=20"
echo.
echo Test finished. You can close this window.
pause
