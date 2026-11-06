@echo off
rem install_pack35.cmd - 3 November: the leader's launcher follows what is killing his team.
rem   LLM\Init.sqs 12, LLM\Report.sqs 20, LLM\Kit.sqs (new) and Main\UpdateIndependentAI.sqs, in the four missions,
rem   in both Missions (trials) and MPMissions (what you host). The relay does not change.
rem   Also tests\run_tests.py (checks Kit.sqs too) and sync_mpmissions.cmd (checks the new versions).
rem It first checks every file it replaces is the one Claude built from; if any is not, it changes nothing.
rem What it replaces goes to C:\ofp-llm\backup\20261103_pack35.
setlocal
set "P=C:\ofp-llm\pack35"
set "B=C:\ofp-llm\backup\20261103_pack35"
set "DOCS=C:\Users\tumbl\Documents\Cold War Assault"
set "MS=mfcti116a_llmv1a.noe mfcti116a_stock.noe mfcti116a_llmv1a.Eden mfcti116a_stock.Eden"
set "BAD="
netstat -ano | findstr ":8777" | findstr "LISTENING" >nul && (echo A relay is still running. Close the game and the relay, then run this again.& pause & goto :eof)

echo Checking the files to be replaced...
for %%d in (Missions MPMissions) do for %%m in (%MS%) do call :check "%%d" "%%m"
if defined BAD echo.& echo Nothing was changed. Tell Claude which lines say DIFFERENT or MISSING.& pause & goto :eof

echo Installing...
for %%d in (Missions MPMissions) do for %%m in (%MS%) do call :install "%%d" "%%m"
mkdir "%B%\top\tests" 2>nul
copy /y "C:\ofp-llm\tests\run_tests.py" "%B%\top\tests\run_tests.py" >nul
copy /y "C:\ofp-llm\sync_mpmissions.cmd" "%B%\top\sync_mpmissions.cmd" >nul
copy /y "%P%\top\tests\run_tests.py" "C:\ofp-llm\tests\run_tests.py" >nul
copy /y "%P%\top\sync_mpmissions.cmd" "C:\ofp-llm\sync_mpmissions.cmd" >nul

echo.
echo Installed now:
for %%d in (Missions MPMissions) do for %%m in (%MS%) do call :show "%%d" "%%m"
echo.
python C:\ofp-llm\tests\run_tests.py
echo.
if defined BAD (echo Finished with a problem. Tell Claude.) else (echo Done. The tests must say 18 of 18 groups. Tell Claude.)
pause
goto :eof

:check
for %%f in (LLM\Init.sqs LLM\Report.sqs Main\UpdateIndependentAI.sqs) do (
  if not exist "%DOCS%\%~1\%~2\%%f" (echo    MISSING   %~1\%~2\%%f& set "BAD=1") else (
    fc /b "%DOCS%\%~1\%~2\%%f" "%P%\known\%~2\%%f" >nul || (echo    DIFFERENT %~1\%~2\%%f& set "BAD=1")
  )
)
goto :eof

:install
for %%f in (LLM\Init.sqs LLM\Report.sqs Main\UpdateIndependentAI.sqs) do (
  if not exist "%B%\%~1\%~2\LLM" mkdir "%B%\%~1\%~2\LLM" "%B%\%~1\%~2\Main" 2>nul
  copy /y "%DOCS%\%~1\%~2\%%f" "%B%\%~1\%~2\%%f" >nul
  copy /y "%P%\new\%~2\%%f" "%DOCS%\%~1\%~2\%%f" >nul || set "BAD=1"
)
copy /y "%P%\new\%~2\LLM\Kit.sqs" "%DOCS%\%~1\%~2\LLM\Kit.sqs" >nul || set "BAD=1"
goto :eof

:show
set "OK=1"
findstr /c:"(version 12)" "%DOCS%\%~1\%~2\LLM\Init.sqs" >nul || set "OK="
findstr /c:"(version 20)" "%DOCS%\%~1\%~2\LLM\Report.sqs" >nul || set "OK="
findstr /c:"LLM\Kit.sqs" "%DOCS%\%~1\%~2\Main\UpdateIndependentAI.sqs" >nul || set "OK="
if not exist "%DOCS%\%~1\%~2\LLM\Kit.sqs" set "OK="
if defined OK (echo    %~1\%~2: current) else (echo    %~1\%~2: COPY FAILED& set "BAD=1")
goto :eof
