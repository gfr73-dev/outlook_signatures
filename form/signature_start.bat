@echo off
REM Optional: activate virtual environment
REM call venv\Scripts\activate

REM Launch Flask app
set FLASK_APP=app.py
set FLASK_ENV=development
python -m flask run --host=0.0.0.0 --port=5001

pause
