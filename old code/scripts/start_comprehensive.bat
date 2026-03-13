@echo off
REM One-command starter for comprehensive job board crawl (moved to scripts)

cd /d "%~dp0"
cd ..
set REPO_ROOT=%cd%
cd "%~dp0"

call run_crawler.bat extensive --engine brave --pages 2 --rate 1.0

