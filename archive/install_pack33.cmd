@echo off
rem install_pack33.cmd - 22 October: the air response, and the scorecard.
rem   relay.py version 32, run_trials.ps1 version 19, tests, tools\scorecard.py, and in all four missions, in BOTH
rem   Missions (what the trials use) and MPMissions (what you host): LLM\Report.sqs version 19 and LLM\AirBuy.sqs.
rem It stops if a relay is running. Each Report.sqs must first be the pack 32 one, or already the new one; if any
rem is not, nothing is changed. What it replaces goes to C:\ofp-llm\backup\20261022_pack33.
setlocal
set "D=C:\Users\tumbl\Documents\Cold War Assault"
set "P=C:\ofp-llm\pack33"
set "B=C:\ofp-llm\backup\20261022_pack33"
netstat -ano | findstr ":8777" | findstr "LISTENING" >nul && (echo A relay is still running ^(a trial or a game^). Close it, then run this again.& pause & goto :eof)
set BAD=0
for %%r in (Missions MPMissions) do for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe mfcti116a_llmv1a.Eden mfcti116a_stock.Eden) do call :check %%r %%m
if "%BAD%"=="0" goto install
echo.
echo NOTHING WAS CHANGED: the files marked above are not ones this pack knows.
echo Tell Claude which ones, so it can make the pack from your files.
pause
goto :eof

:install
mkdir "%B%\tests" 2>nul
mkdir "%B%\tools" 2>nul
mkdir "C:\ofp-llm\tools" 2>nul
for %%f in (relay.py run_trials.ps1 tests\run_tests.py tests\README.txt tests\test_rules_v26.py tests\test_rules_v29.py) do if not exist "%B%\%%f" copy /y "C:\ofp-llm\%%f" "%B%\%%f" >nul
for %%f in (relay.py run_trials.ps1 tests\run_tests.py tests\README.txt tests\test_rules_v26.py tests\test_rules_v29.py tests\test_rules_v32.py tools\scorecard.py) do copy /y "%P%\top\%%f" "C:\ofp-llm\%%f" >nul
for %%r in (Missions MPMissions) do for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe mfcti116a_llmv1a.Eden mfcti116a_stock.Eden) do call :one %%r %%m
echo.
findstr /c:"VERSION = 32" "C:\ofp-llm\relay.py" >nul && (echo relay.py version 32 installed) || (echo relay.py COPY FAILED)
findstr /c:"(version 19)" "C:\ofp-llm\run_trials.ps1" >nul && (echo run_trials.ps1 version 19 installed) || (echo run_trials.ps1 COPY FAILED)
for %%r in (Missions MPMissions) do for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe mfcti116a_llmv1a.Eden mfcti116a_stock.Eden) do (
  if exist "%D%\%%r\%%m" (findstr /c:"(version 19)" "%D%\%%r\%%m\LLM\Report.sqs" >nul && (echo %%r\%%m: version 19 installed) || (echo %%r\%%m: COPY FAILED))
)
echo.
python C:\ofp-llm\tests\run_tests.py
echo.
echo Done. Every line above must say installed, and the tests 18 of 18 groups.
pause
goto :eof

:check
if not exist "%D%\%1\%2" (echo %1\%2: not there, skipped& goto :eof)
if exist "%D%\%1\%2\LLM\AirBuy.sqs" fc /b "%D%\%1\%2\LLM\AirBuy.sqs" "%P%\new\%2\LLM\AirBuy.sqs" >nul 2>&1 || (echo %1\%2\LLM\AirBuy.sqs: NOT A FILE THIS PACK KNOWS& set BAD=1& goto :eof)
fc /b "%D%\%1\%2\LLM\Report.sqs" "%P%\new\%2\LLM\Report.sqs" >nul 2>&1 && (echo %1\%2: already the new version& goto :eof)
fc /b "%D%\%1\%2\LLM\Report.sqs" "%P%\known\%2\LLM\Report.sqs" >nul 2>&1 && (echo %1\%2: as expected& goto :eof)
echo %1\%2\LLM\Report.sqs: NOT A FILE THIS PACK KNOWS
set BAD=1
goto :eof

:one
if not exist "%D%\%1\%2" goto :eof
fc /b "%D%\%1\%2\LLM\Report.sqs" "%P%\new\%2\LLM\Report.sqs" >nul 2>&1 && goto :eof
if not exist "%B%\%1\%2\LLM\Report.sqs" (mkdir "%B%\%1\%2\LLM" 2>nul& copy /y "%D%\%1\%2\LLM\Report.sqs" "%B%\%1\%2\LLM\Report.sqs" >nul)
copy /y "%P%\new\%2\LLM\Report.sqs" "%D%\%1\%2\LLM\Report.sqs" >nul
copy /y "%P%\new\%2\LLM\AirBuy.sqs" "%D%\%1\%2\LLM\AirBuy.sqs" >nul
goto :eof
