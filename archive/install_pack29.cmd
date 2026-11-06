@echo off
rem install_pack29.cmd - 18 October: the mortar crew stops at 4 men, the mortars lift fire near our own teams,
rem and the rounds they fire are counted. Into both missions:
rem   LLM\Init.sqs version 9, LLM\Report.sqs version 17, Main\UpdateIndependentAI.sqs with the crew cap.
rem It first checks that each of the 6 files is the one this pack was made from (or already the new one).
rem If any is not, it changes nothing. What it replaces is copied to C:\ofp-llm\backup\20261018_pack29 first.
setlocal
set "M=C:\Users\tumbl\Documents\Cold War Assault\Missions"
set "P=C:\ofp-llm\pack29"
set "B=C:\ofp-llm\backup\20261018_pack29"
set BAD=0
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe) do for %%f in (LLM\Init.sqs LLM\Report.sqs Main\UpdateIndependentAI.sqs) do call :check %%m %%f
if "%BAD%"=="0" goto install
echo.
echo NOTHING WAS CHANGED: the files marked above are not the ones this pack was made from.
echo Tell Claude which ones, so it can make the pack from your files.
pause
goto :eof

:install
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe) do for %%f in (LLM\Init.sqs LLM\Report.sqs Main\UpdateIndependentAI.sqs) do call :one %%m %%f
echo.
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe) do (
  findstr /c:"(version 17)" "%M%\%%m\LLM\Report.sqs" >nul && (echo %%m: Report.sqs version 17 installed) || (echo %%m: Report.sqs COPY FAILED)
  findstr /c:"(version 9)" "%M%\%%m\LLM\Init.sqs" >nul && (echo %%m: Init.sqs version 9 installed) || (echo %%m: Init.sqs COPY FAILED)
  findstr /c:"llmCrewMax" "%M%\%%m\Main\UpdateIndependentAI.sqs" >nul && (echo %%m: UpdateIndependentAI.sqs crew cap installed) || (echo %%m: UpdateIndependentAI.sqs COPY FAILED)
)
echo.
python C:\ofp-llm\tests\run_tests.py
echo.
echo Done. All six mission lines must say installed, and the tests 15 of 15 groups.
pause
goto :eof

:check
if not exist "%M%\%1\%2" (echo MISSING: %1\%2& set BAD=1& goto :eof)
fc /b "%M%\%1\%2" "%P%\new\%1\%2" >nul 2>&1 && (echo %1\%2: already the new version& goto :eof)
fc /b "%M%\%1\%2" "%P%\base\%1\%2" >nul 2>&1 && (echo %1\%2: as expected& goto :eof)
echo %1\%2: NOT THE FILE THIS PACK WAS MADE FROM
set BAD=1
goto :eof

:one
if not exist "%B%\%1\%2" (mkdir "%B%\%1\LLM" 2>nul& mkdir "%B%\%1\Main" 2>nul& copy /y "%M%\%1\%2" "%B%\%1\%2" >nul)
copy /y "%P%\new\%1\%2" "%M%\%1\%2" >nul
goto :eof
