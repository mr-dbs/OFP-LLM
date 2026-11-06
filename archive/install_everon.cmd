@echo off
rem install_everon.cmd - 18 October: the LLM commander on Everon. Adds two missions to your Missions folder:
rem   mfcti116a_llmv1a.Eden  "MFCTI 1.16a Coop Everon LLM"                    the LLM commands East
rem   mfcti116a_stock.Eden   "MFCTI 1.16a Coop Everon LLM (stock commander)"  the stock commander, for comparison
rem Made from the pack 29 scripts of the Nogova missions and the map of MFCTI_1.16_Coop_Everon.Eden.pbo.
rem Nothing of the Nogova missions is touched. If an Everon folder is already there, it is moved to
rem C:\ofp-llm\backup\20261018_everon first.
setlocal
set "M=C:\Users\tumbl\Documents\Cold War Assault\Missions"
set "B=C:\ofp-llm\backup\20261018_everon"
if not exist "C:\ofp-llm\pack30\everon_missions.zip" (echo MISSING: C:\ofp-llm\pack30\everon_missions.zip & pause & goto :eof)
for %%m in (mfcti116a_llmv1a.Eden mfcti116a_stock.Eden) do if exist "%M%\%%m" (mkdir "%B%" 2>nul & move "%M%\%%m" "%B%\%%m_%RANDOM%" >nul & echo moved the old %%m to %B%)
powershell -NoProfile -Command "Expand-Archive -Force -Path 'C:\ofp-llm\pack30\everon_missions.zip' -DestinationPath '%M%'"
echo.
for %%m in (mfcti116a_llmv1a.Eden mfcti116a_stock.Eden) do (
  findstr /c:"(version 17)" "%M%\%%m\LLM\Report.sqs" >nul && (echo %%m: installed, Report.sqs version 17) || (echo %%m: INSTALL FAILED)
)
echo.
python C:\ofp-llm\tests\run_tests.py
echo.
echo Done. Both mission lines must say installed, and the tests 15 of 15 groups.
pause
