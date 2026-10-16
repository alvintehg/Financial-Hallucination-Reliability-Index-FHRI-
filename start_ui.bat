@echo off
echo ============================================================
echo Starting LLM Financial Chatbot Web UI
echo ============================================================
echo.
echo IMPORTANT: Make sure the server is running first!
echo (Run start_server.bat in another window)
echo.
echo The UI will open in your browser automatically
echo.
echo ============================================================
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat
streamlit run src/demo_streamlit.py

pause
