@echo off
rem install_pack31.cmd - 18 October: the commander's guard, in all four missions (Nogova and Everon, LLM and stock):
rem   LLM\Init.sqs version 10, LLM\Report.sqs version 18, Main\UpdateIndependentAI.sqs with the crew cap (pack 29).
rem East keeps 4 HE stations at its base besides the 2 mortars, and its commander buys one soldier per gun into
rem his own team to man them. Each file must first be one this pack knows (pack 28, pack 29 or the Everon build),
rem or already the new one; if any is not, nothing is changed. Replaced files go to C:\ofp-llm\backup\20261018_pack31.
setlocal
set "M=C:\Users\tumbl\Documents\Cold War Assault\Missions"
set "P=C:\ofp-llm\pack31"
set "B=C:\ofp-llm\backup\20261018_pack31"
set BAD=0
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe mfcti116a_llmv1a.Eden mfcti116a_stock.Eden) do for %%f in (LLM\Init.sqs LLM\Report.sqs Main\UpdateIndependentAI.sqs) do call :check %%m %%f
if "%BAD%"=="0" goto install
echo.
echo NOTHING WAS CHANGED: the files marked above are not ones this pack knows.
echo Tell Claude which ones, so it can make the pack from your files.
pause
goto :eof

:install
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe mfcti116a_llmv1a.Eden mfcti116a_stock.Eden) do for %%f in (LLM\Init.sqs LLM\Report.sqs Main\UpdateIndependentAI.sqs) do call :one %%m %%f
echo.
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe mfcti116a_llmv1a.Eden mfcti116a_stock.Eden) do (
  findstr /c:"(version 18)" "%M%\%%m\LLM\Report.sqs" >nul && (echo %%m: Report.sqs version 18 installed) || (echo %%m: Report.sqs COPY FAILED)
  findstr /c:"(version 10)" "%M%\%%m\LLM\Init.sqs" >nul && (echo %%m: Init.sqs version 10 installed) || (echo %%m: Init.sqs COPY FAILED)
)
echo.
python C:\ofp-llm\tests\run_tests.py
echo.
echo Done. All eight mission lines must say installed, and the tests 16 of 16 groups.
pause
goto :eof

:check
set OK=0
if not exist "%M%\%1\%2" (echo MISSING: %1\%2& set BAD=1& goto :eof)
fc /b "%M%\%1\%2" "%P%\new\%1\%2" >nul 2>&1 && (echo %1\%2: already the new version& goto :eof)
for %%k in ("%P%\known\%1\%2.*") do fc /b "%M%\%1\%2" "%%~k" >nul 2>&1 && set OK=1
if "%OK%"=="1" (echo %1\%2: as expected& goto :eof)
echo %1\%2: NOT A FILE THIS PACK KNOWS
set BAD=1
goto :eof

:one
fc /b "%M%\%1\%2" "%P%\new\%1\%2" >nul 2>&1 && goto :eof
if not exist "%B%\%1\%2" (mkdir "%B%\%1\LLM" 2>nul& mkdir "%B%\%1\Main" 2>nul& copy /y "%M%\%1\%2" "%B%\%1\%2" >nul)
copy /y "%P%\new\%1\%2" "%M%\%1\%2" >nul
goto :eof
