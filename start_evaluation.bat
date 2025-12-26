@echo off
echo Starting backend server for evaluation...
echo.
echo Make sure you have activated your virtual environment first!
echo.
venv\Scripts\activate
uvicorn src.server:app --port 8000






























