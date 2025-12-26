@echo off
echo ========================================
echo Restarting AI Advisor Application
echo ========================================
echo.
echo Stopping any running instances...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Streamlit*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting Streamlit app...
echo.
echo The app will open in your browser automatically.
echo To stop the app, press Ctrl+C in this window.
echo.
streamlit run src\demo_streamlit.py
