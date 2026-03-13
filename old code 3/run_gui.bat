@echo off
pushd %~dp0\..
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
)
py -3 gui.py %*
popd