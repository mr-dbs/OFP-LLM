@echo off
rem install_pack28.cmd - 17 October: LLM\Report.sqs version 16 into both missions.
rem What it replaces is copied to C:\ofp-llm\backup\20261017_pack28 first (only the first time it runs).
setlocal
set "M=C:\Users\tumbl\Documents\Cold War Assault\Missions"
set "B=C:\ofp-llm\backup\20261017_pack28"
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe) do (call :one %%m LLM Report.sqs)
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe) do findstr /c:"(version 16)" "%M%\%%m\LLM\Report.sqs" >nul && (echo %%m: Report.sqs version 16 installed) || (echo %%m: COPY FAILED)
echo.
python C:\ofp-llm\tests\run_tests.py
echo.
echo Done. Both mission lines must say version 16, and the tests 14 of 14 groups.
pause
goto :eof

:one
if not exist "%M%\%1\%2\%3" (echo MISSING: "%M%\%1\%2\%3" & goto :eof)
if not exist "%B%\%1\%2\%3" (mkdir "%B%\%1\%2" 2>nul & copy /y "%M%\%1\%2\%3" "%B%\%1\%2\%3" >nul)
copy /y "C:\ofp-llm\pack28\%1\%2\%3" "%M%\%1\%2\%3" >nul
goto :eof
