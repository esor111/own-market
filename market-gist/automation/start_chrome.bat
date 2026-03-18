@echo off
echo Starting Chrome with remote debugging...
echo.
echo IMPORTANT: 
echo 1. Chrome will open with a separate profile
echo 2. Navigate to https://nepsealpha.com/nepse-chart manually
echo 3. Then run: python analyze_stock.py SMHL 1W
echo.
echo Press any key to start Chrome...
pause > nul

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-automation" https://nepsealpha.com/nepse-chart

echo.
echo Chrome started! Wait for the page to load, then run the Python script.
