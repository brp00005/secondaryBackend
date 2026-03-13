#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
Push-Location (Join-Path $PSScriptRoot '..')
if (Test-Path '.venv/Scripts/Activate.ps1') {
    . .venv/Scripts/Activate.ps1
}
python gui.py $args
Pop-Location