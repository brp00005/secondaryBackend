# Job Board Crawler - Windows PowerShell execution script
# Usage: .\run_crawler.ps1 [mode] [options]

param(
    [Parameter(Position = 0)]
    [string]$Mode = "quick",
    
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ExtraArgs
)

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommandPath
$VenvPath = Join-Path $ScriptDir ".venv"
$OutputDir = Join-Path $ScriptDir "output"
$PythonExe = Join-Path $VenvPath "Scripts" "python.exe"

# Colors
$Green = 'Green'
$Red = 'Red'
$Yellow = 'Yellow'
$Blue = 'Cyan'

function Print-Banner {
    Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor $Blue
    Write-Host "║     Job Board Discovery Crawler v1.0       ║" -ForegroundColor $Blue
    Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor $Blue
    Write-Host ""
}

function Print-Usage {
    Write-Host "Usage: .\run_crawler.ps1 [MODE] [OPTIONS]" -ForegroundColor $Yellow
    Write-Host ""
    Write-Host "MODES:"
    Write-Host "  quick       - Discover 10 job boards (default)"
    Write-Host "  standard    - Discover 50 job boards"
    Write-Host "  extensive   - Discover 100+ job boards with career pages"
    Write-Host "  resume      - Resume from last checkpoint"
    Write-Host "  test        - Run unit tests only"
    Write-Host ""
    Write-Host "OPTIONS:"
    Write-Host "  -Help       - Show this message"
    Write-Host "  -Limit N    - Override limit (e.g., -Limit 25)"
    Write-Host ""
    Write-Host "EXAMPLES:"
    Write-Host "  .\run_crawler.ps1 quick"
    Write-Host "  .\run_crawler.ps1 standard"
    Write-Host "  .\run_crawler.ps1 extensive -Limit 75"
    Write-Host "  .\run_crawler.ps1 resume"
    Write-Host ""
}

function Check-VirtualEnv {
    if (-not (Test-Path $VenvPath)) {
        Write-Host "✗ Virtual environment not found at $VenvPath" -ForegroundColor $Red
        Write-Host "Please run: python -m venv $VenvPath" -ForegroundColor $Yellow
        exit 1
    }
    
    if (-not (Test-Path $PythonExe)) {
        Write-Host "✗ Python executable not found" -ForegroundColor $Red
        exit 1
    }
    
    Write-Host "✓ Virtual environment ready" -ForegroundColor $Green
}

function Create-OutputDir {
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir | Out-Null
    }
    Write-Host "✓ Output directory ready: $OutputDir" -ForegroundColor $Green
}

function Run-Crawler {
    param(
        [string]$CrawlMode,
        [string[]]$Args
    )
    
    $Limit = 10
    $DetectCareers = ""
    $OutputName = "job_discovery"
    
    switch ($CrawlMode.ToLower()) {
        "quick" {
            $Limit = 10
            $OutputName = "quick_discovery"
        }
        "standard" {
            $Limit = 50
            $OutputName = "standard_discovery"
        }
        "extensive" {
            $Limit = 100
            $DetectCareers = "--detect-careers"
            $OutputName = "extensive_discovery"
        }
        "resume" {
            Write-Host "🔄 Resuming from last checkpoint..." -ForegroundColor $Blue
            & $PythonExe run.py --engine brave --filter --resume @Args
            return $LASTEXITCODE
        }
        "test" {
            Write-Host "🧪 Running unit tests..." -ForegroundColor $Blue
            & $PythonExe -c @"
from crawler import DuckDuckGoJobBoardCrawler
import sys
print("\n" + "="*60)
print("UNIT TESTS")
print("="*60)

c = DuckDuckGoJobBoardCrawler()
tests_passed = 0
tests_total = 0

# Aggregator detection
tests = [
    ('https://indeed.com', True),
    ('https://linkedin.com', True),
    ('https://glassdoor.com', True),
    ('https://acme.com', False)
]

for url, expected in tests:
    result = c.is_job_aggregator(url)
    tests_total += 1
    if result == expected:
        tests_passed += 1
        print(f'✓ Aggregator: {url}')
    else:
        print(f'✗ Aggregator: {url} (expected {expected}, got {result})')

print("\n" + "="*60)
print(f"Tests: {tests_passed}/{tests_total} passed")
print("="*60)

sys.exit(0 if tests_passed == tests_total else 1)
"@
            return $LASTEXITCODE
        }
        default {
            Write-Host "✗ Unknown mode: $CrawlMode" -ForegroundColor $Red
            Print-Usage
            exit 1
        }
    }
    
    Write-Host "🕷️  Crawling job boards (limit: $Limit)..." -ForegroundColor $Blue
    $OutputPath = Join-Path "output" $OutputName
    & $PythonExe run.py --engine brave --filter --limit $Limit $DetectCareers --output $OutputPath @Args
    return $LASTEXITCODE
}

# Main execution
if ($Mode -eq "-Help" -or $Mode -eq "--help" -or $Mode -eq "?") {
    Print-Usage
    exit 0
}

Print-Banner
Check-VirtualEnv
Create-OutputDir

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Blue
Write-Host ""

$ExitCode = Run-Crawler $Mode $ExtraArgs

if ($ExitCode -eq 0) {
    Write-Host ""
    Write-Host "✓ Crawler completed successfully!" -ForegroundColor $Green
    Write-Host "📂 Results saved to: $OutputDir" -ForegroundColor $Blue
    Write-Host ""
    Get-ChildItem "$OutputDir\*.xlsx" -ErrorAction SilentlyContinue | ForEach-Object {
        $size = "{0:N0}" -f $_.Length
        Write-Host "   $($_.Name) ($size bytes)"
    }
    Write-Host ""
    exit 0
}
else {
    Write-Host ""
    Write-Host "✗ Crawler encountered an error" -ForegroundColor $Red
    exit 1
}
