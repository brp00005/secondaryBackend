@echo off
REM Start script for Chamber crawler (Windows CMD)
cd /d %~dp0\..
IF EXIST .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
)
if not exist output mkdir output
echo Initializing chamber database to output\chamber_database.xlsx...
python chamber_scraper.py --db output\chamber_database.xlsx
echo Done. File: output\chamber_database.xlsx
