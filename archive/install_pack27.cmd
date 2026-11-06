@echo off
rem install_pack27.cmd - 15 October: LLM\Report.sqs version 15 and Main\UpdateCommanderAI.sqs into both missions.
rem What it replaces is copied to C:\ofp-llm\backup\20261015_pack27 first (only the first time it runs).
setlocal
set "M=C:\Users\tumbl\Documents\Cold War Assault\Missions"
set "B=C:\ofp-llm\backup\20261015_pack27"
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe) do (call :one %%m LLM Report.sqs & call :one %%m Main UpdateCommanderAI.sqs)
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe) do findstr /c:"(version 15)" "%M%\%%m\LLM\Report.sqs" >nul && (echo %%m: Report.sqs version 15 installed) || (echo %%m: COPY FAILED)
echo.
python C:\ofp-llm\tests\run_tests.py
echo.
echo Done. Both mission lines must say version 15, and the tests 13 of 13 groups.
pause
goto :eof

:one
if not exist "%M%\%1\%2\%3" (echo MISSING: "%M%\%1\%2\%3" & goto :eof)
if not exist "%B%\%1\%2\%3" (mkdir "%B%\%1\%2" 2>nul & copy /y "%M%\%1\%2\%3" "%B%\%1\%2\%3" >nul)
copy /y "C:\ofp-llm\pack27\%1\%2\%3" "%M%\%1\%2\%3" >nul
goto :eof
