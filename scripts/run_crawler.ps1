param(
    [Parameter(Position = 0)]
    [string]$Mode = "quick",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ExtraArgs
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommandPath
$RepoRoot = Split-Path -Parent $ScriptDir
$VenvPath = Join-Path $RepoRoot ".venv"
$OutputDir = Join-Path $RepoRoot "output"
$PythonExe = Join-Path $VenvPath "Scripts" "python.exe"

function Print-Banner { Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan; Write-Host "║     Job Board Discovery Crawler v1.0       ║" -ForegroundColor Cyan; Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan }
function Print-Usage { Write-Host "Usage: .\scripts\run_crawler.ps1 [MODE] [OPTIONS]" -ForegroundColor Yellow }
function Check-VirtualEnv { if (-not (Test-Path $VenvPath)) { Write-Host "✗ Virtual environment not found at $VenvPath" -ForegroundColor Red; exit 1 } if (-not (Test-Path $PythonExe)) { Write-Host "✗ Python executable not found" -ForegroundColor Red; exit 1 } }
function Create-OutputDir { if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir | Out-Null } Write-Host "✓ Output directory ready: $OutputDir" -ForegroundColor Green }

function Run-Crawler {
    param([string]$CrawlMode, [string[]]$Args)
    $Limit = 10; $DetectCareers = ""; $OutputName = "job_discovery"
    switch ($CrawlMode.ToLower()) {
        "quick" { $Limit = 10; $OutputName = "quick_discovery" }
        "standard" { $Limit = 50; $OutputName = "standard_discovery" }
        "extensive" { $Limit = 100; $DetectCareers = "--detect-careers"; $OutputName = "extensive_discovery" }
        "resume" { & $PythonExe "$RepoRoot/run.py" --engine brave --filter --resume @Args; return $LASTEXITCODE }
        "test" { & $PythonExe -c "from crawler import DuckDuckGoJobBoardCrawler; print('test')"; return $LASTEXITCODE }
        default { Print-Usage; exit 1 }
    }
    & $PythonExe "$RepoRoot/run.py" --engine brave --filter --limit $Limit $DetectCareers --output (Join-Path $OutputDir $OutputName) @Args
    return $LASTEXITCODE
}

if ($Mode -eq "-Help" -or $Mode -eq "--help" -or $Mode -eq "?") { Print-Usage; exit 0 }
Print-Banner; Check-VirtualEnv; Create-OutputDir
$ExitCode = Run-Crawler $Mode $ExtraArgs
exit $ExitCode
