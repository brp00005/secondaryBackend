# One-command starter for comprehensive job board crawl (moved to scripts)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommandPath
Set-Location $ScriptDir

& .\run_crawler.ps1 extensive --engine brave --pages 2 --rate 1.0
exit $LASTEXITCODE
