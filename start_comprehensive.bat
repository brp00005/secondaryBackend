@echo off
REM One-command starter for comprehensive job board crawl (Windows CMD)

cd /d "%~dp0"
call run_crawler.bat extensive --engine brave --pages 2 --rate 1.0
