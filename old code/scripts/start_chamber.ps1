#!/usr/bin/env pwsh
<# Start script for Chamber crawler (PowerShell) #>
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir\..\
if (Test-Path .venv/Scripts/Activate.ps1) {
    . .venv/Scripts/Activate.ps1
}
New-Item -ItemType Directory -Force -Path output | Out-Null
Write-Output "Initializing chamber database to output/chamber_database.xlsx..."
python chamber_scraper.py --db output/chamber_database.xlsx
Write-Output "Done. File: output/chamber_database.xlsx"