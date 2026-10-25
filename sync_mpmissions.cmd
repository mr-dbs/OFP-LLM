@echo off
rem sync_mpmissions.cmd - 22 October: copies the four current LLM missions from Missions (what the trials use)
rem into MPMissions (what the game's host list shows), so the game you host runs the same scripts as the trials.
rem Any copy already in MPMissions is moved to C:\ofp-llm\backup\mpmissions_<date> first. Run it after every install.
setlocal
set "SRC=C:\Users\tumbl\Documents\Cold War Assault\Missions"
set "DST=C:\Users\tumbl\Documents\Cold War Assault\MPMissions"
set "B=C:\ofp-llm\backup\mpmissions_%DATE:~-4%%DATE:~4,2%%DATE:~7,2%"
netstat -ano | findstr ":8777" | findstr "LISTENING" >nul && (echo A relay is running. Close the game and the relay first.& pause & goto :eof)
if not exist "%DST%" mkdir "%DST%"
echo What MPMissions holds now:
dir /b /ad "%DST%\mfcti116a*" 2>nul
for /d %%m in ("%DST%\mfcti116a*") do if exist "%%m\LLM\Report.sqs" (for /f "delims=" %%v in ('findstr /c:"Report.sqs (version" "%%m\LLM\Report.sqs"') do echo    %%~nxm: %%v)
echo.
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe mfcti116a_llmv1a.Eden mfcti116a_stock.Eden) do call :one %%m
echo.
echo MPMissions now:
for %%m in (mfcti116a_llmv1a.noe mfcti116a_stock.noe mfcti116a_llmv1a.Eden mfcti116a_stock.Eden) do (
  findstr /c:"(version 18)" "%DST%\%%m\LLM\Report.sqs" >nul && findstr /c:"(version 11)" "%DST%\%%m\LLM\Init.sqs" >nul && (echo    %%m: current) || (echo    %%m: COPY FAILED)
)
echo.
echo Done. Copy the whole window text to Claude if anything says FAILED.
pause
goto :eof

:one
if not exist "%SRC%\%1\LLM\Report.sqs" (echo MISSING in Missions: %1& goto :eof)
if exist "%DST%\%1" (mkdir "%B%" 2>nul & move "%DST%\%1" "%B%\%1_%RANDOM%" >nul & echo moved the old MPMissions\%1 to %B%)
robocopy "%SRC%\%1" "%DST%\%1" /E /NFL /NDL /NJH /NJS /NP >nul
echo copied %1
goto :eof
