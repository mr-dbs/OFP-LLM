@echo off
rem install_pack34.cmd - 25 October: relay.py version 33. The air response now also starts for an enemy transport
rem helicopter such as an armed UH-60. Only relay.py and one test change. The old relay goes to backup\20261025_pack34.
setlocal
set "P=C:\ofp-llm\pack34"
set "B=C:\ofp-llm\backup\20261025_pack34"
netstat -ano | findstr ":8777" | findstr "LISTENING" >nul && (echo A relay is still running. Close it, then run this again.& pause & goto :eof)
mkdir "%B%\tests" 2>nul
if not exist "%B%\relay.py" copy /y "C:\ofp-llm\relay.py" "%B%\relay.py" >nul
if not exist "%B%\tests\test_rules_v32.py" copy /y "C:\ofp-llm\tests\test_rules_v32.py" "%B%\tests\test_rules_v32.py" >nul
copy /y "%P%\top\relay.py" "C:\ofp-llm\relay.py" >nul
copy /y "%P%\top\tests\test_rules_v32.py" "C:\ofp-llm\tests\test_rules_v32.py" >nul
findstr /c:"VERSION = 33" "C:\ofp-llm\relay.py" >nul && (echo relay.py version 33 installed) || (echo relay.py COPY FAILED)
echo.
python C:\ofp-llm\tests\run_tests.py
echo.
echo Done. The tests must say 18 of 18 groups.
pause
