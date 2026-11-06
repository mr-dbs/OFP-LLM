@echo off
rem install_pack32.cmd - 19 October: both sides under the relay, and equal funds.
rem   relay.py version 31 (--rules-side), run_trials.ps1 version 18 (kinds duel and head, -Funds), tests,
rem   and in all four missions LLM\Init.sqs version 11 (llmTestSides and llmTestFunds in LLM\TestStart.sqf).
rem Run it after the trial that is running now has finished: it stops if a relay is still running.
rem Each mission file must first be one this pack knows, or already the new one; if any is not, nothing is changed.
rem What it replaces goes to C:\ofp-llm\backup\20261019_pack32.
setlocal
set "M=C:\Users\tumbl\Documents\Cold War Assault\Missions"
set "P=C:\ofp-llm\pack32"
set "B=C:\ofp-llm\backup\20261019_pack32"
netstat -ano | findstr ":8777" | findstr "LISTENING" >nul && (echo A relay is still running ^(a trial or a game^). Let it finish or close it, then run this again.& pause & goto :eof)
set BAD=0
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe mfcti116a_llmv1a.Eden mfcti116a_stock.Eden) do for %%f in (LLM\Init.sqs LLM\Report.sqs Main\UpdateIndependentAI.sqs) do call :check %%m %%f
if "%BAD%"=="0" goto install
echo.
echo NOTHING WAS CHANGED: the files marked above are not ones this pack knows.
echo Tell Claude which ones, so it can make the pack from your files.
pause
goto :eof

:install
mkdir "%B%\tests" 2>nul
for %%f in (relay.py run_trials.ps1 tests\run_tests.py tests\README.txt) do if not exist "%B%\%%f" copy /y "C:\ofp-llm\%%f" "%B%\%%f" >nul
for %%f in (relay.py run_trials.ps1 tests\run_tests.py tests\README.txt tests\test_rules_v31.py) do copy /y "%P%\top\%%f" "C:\ofp-llm\%%f" >nul
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe mfcti116a_llmv1a.Eden mfcti116a_stock.Eden) do for %%f in (LLM\Init.sqs LLM\Report.sqs Main\UpdateIndependentAI.sqs) do call :one %%m %%f
echo.
findstr /c:"VERSION = 31" "C:\ofp-llm\relay.py" >nul && (echo relay.py version 31 installed) || (echo relay.py COPY FAILED)
findstr /c:"(version 18)" "C:\ofp-llm\run_trials.ps1" >nul && (echo run_trials.ps1 version 18 installed) || (echo run_trials.ps1 COPY FAILED)
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe mfcti116a_llmv1a.Eden mfcti116a_stock.Eden) do (
  findstr /c:"(version 11)" "%M%\%%m\LLM\Init.sqs" >nul && (echo %%m: Init.sqs version 11 installed) || (echo %%m: Init.sqs COPY FAILED)
)
echo.
python C:\ofp-llm\tests\run_tests.py
echo.
echo Done. Every line above must say installed, and the tests 17 of 17 groups.
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
