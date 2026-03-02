# Quick Start Execution Scripts

Three easy-to-use scripts for running the Job Board Crawler on different operating systems.

## Available Scripts

| OS | Script | Command |
|---|---|---|
| 🐧 Linux/macOS | `scripts/run_crawler.sh` | `./scripts/run_crawler.sh [mode]` |
| 🪟 Windows (CMD) | `scripts/run_crawler.bat` | `scripts\run_crawler.bat [mode]` |
| 🪟 Windows (PowerShell) | `scripts/run_crawler.ps1` | `.\scripts\run_crawler.ps1 [mode]` |

## One-Command Comprehensive Startup

Use these scripts to run a comprehensive crawl in one command (extensive mode + Brave engine + 2 pages/query):

| OS | Script | One command |
|---|---|---|
| 🐧 Linux/macOS | `scripts/start_comprehensive.sh` | `./scripts/start_comprehensive.sh` |
| 🪟 Windows (CMD) | `scripts/start_comprehensive.bat` | `scripts\start_comprehensive.bat` |
| 🪟 Windows (PowerShell) | `scripts/start_comprehensive.ps1` | `.\scripts\start_comprehensive.ps1` |

## Modes

All scripts support these modes:

- **quick** (default) - Discover 10 job boards in ~2-3 minutes
- **standard** - Discover 50 job boards in ~10-15 minutes  
- **extensive** - Discover 100+ job boards with career page detection in 20-30+ minutes
- **resume** - Continue from last checkpoint without starting over
- **test** - Run unit tests only

## Usage Examples

### Linux/macOS
```bash
# One-command comprehensive crawl
./scripts/start_comprehensive.sh

# Quick discovery (10 boards)
./run_crawler.sh quick

# Standard discovery (50 boards)
./run_crawler.sh standard

# Extensive with career pages (100+ boards)
./run_crawler.sh extensive

# Resume from checkpoint
./run_crawler.sh resume

# Run tests
./run_crawler.sh test

# Discover 25 NEW job boards, then stop
./run_crawler.sh quick --discover 25
```

### Windows (Command Prompt/CMD)
```cmd
REM One-command comprehensive crawl
scripts\start_comprehensive.bat

REM Quick discovery
run_crawler.bat quick

REM Standard discovery
run_crawler.bat standard

REM Extensive discovery
run_crawler.bat extensive

REM Resume from checkpoint
run_crawler.bat resume

REM Run tests
run_crawler.bat test
```

### Windows (PowerShell)
```powershell
# One-command comprehensive crawl
.\scripts\start_comprehensive.ps1

# Quick discovery
.\run_crawler.ps1 quick

# Standard discovery
.\run_crawler.ps1 standard

# Extensive discovery
.\run_crawler.ps1 extensive

# Resume from checkpoint
.\run_crawler.ps1 resume

# Run tests
.\run_crawler.ps1 test

# Discover 25 NEW job boards, then stop
.\run_crawler.ps1 quick --discover 25
```

## First Time Setup

Before running any script, ensure the virtual environment is created:

### Linux/macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows (CMD)
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Windows (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## What Each Script Does

1. ✓ Checks virtual environment exists
2. ✓ Creates `output/` directory if needed
3. ✓ Runs the crawler with selected mode
4. ✓ Displays results with file sizes
5. ✓ Saves checkpoint for resume capability

## Output

After running, results are saved to:
- `output/[mode]_discovery_companies.xlsx` - Company career pages
- `output/[mode]_discovery_aggregators.xlsx` - Job aggregator sites
- `output/.crawler_checkpoint.json` - Resume checkpoint (hidden)

`--discover N` (or `--limit N`) stops the crawl once N NEW job boards are discovered during the current run.

## Script Features

All scripts include:
- 🎨 Color-coded output for easy reading
- 📊 Progress indicators and status messages
- 🔄 Automatic virtual environment activation
- 📁 Output directory management
- 🧪 Built-in test mode
- 💾 Checkpoint/resume support

## Troubleshooting

### "Virtual environment not found"
Create it:
```bash
python3 -m venv .venv
```

### "Permission denied" (macOS/Linux)
Make script executable:
```bash
chmod +x run_crawler.sh
```

### PowerShell: "ExecutionPolicy"
Allow scripts to run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Missing Python
Install Python 3.7+ from [python.org](https://www.python.org)

## Notes

- Scripts automatically create `output/` directory
- All output is date-stamped and categorized
- Resume feature allows safe interruption and continuation
- Test mode validates core functionality without network access
- Default timeout is 120 seconds; increase for extensive crawls

## About the Crawler

The Job Board Crawler discovers job boards through Brave Search SERP analysis and categorizes results:
- **Aggregators**: Indeed, LinkedIn, Glassdoor, etc.
- **Company Career Pages**: Company-specific job listings

See [README.md](README.md) and [TEST_SUMMARY.md](TEST_SUMMARY.md) for full documentation.
