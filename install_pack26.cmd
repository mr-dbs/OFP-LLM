@echo off
rem install_pack26.cmd - base defence pack of 12 October: LLM\Report.sqs version 14 into both missions.
rem What it replaces is copied to C:\ofp-llm\backup\20261012_pack26 first (only the first time it runs).
setlocal
set "M=C:\Users\tumbl\Documents\Cold War Assault\Missions"
set "B=C:\ofp-llm\backup\20261012_pack26"
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe) do call :one %%m
echo.
python C:\ofp-llm\tests\run_tests.py
echo.
echo Done. The mission lines above must say version 14, and the tests 12 of 12 groups.
pause
goto :eof

:one
if not exist "%M%\%1\LLM\Report.sqs" (echo MISSING: "%M%\%1\LLM\Report.sqs" & goto :eof)
if not exist "%B%\%1\LLM\Report.sqs" (mkdir "%B%\%1\LLM" 2>nul & copy /y "%M%\%1\LLM\Report.sqs" "%B%\%1\LLM\Report.sqs" >nul)
copy /y "C:\ofp-llm\pack26\%1\LLM\Report.sqs" "%M%\%1\LLM\Report.sqs" >nul
findstr /c:"(version 14)" "%M%\%1\LLM\Report.sqs" >nul && (echo %1: Report.sqs version 14 installed) || (echo %1: COPY FAILED)
goto :eof
