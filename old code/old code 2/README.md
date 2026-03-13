# DuckDuckGo Job Board Crawler

Python crawler that discovers job boards from search results and writes output to exactly two spreadsheets: aggregators and company career boards.

## Quick Start

1. Create a virtualenv and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the crawler:

```bash
# One-command comprehensive crawl (recommended)
./scripts/start_comprehensive.sh

# Discover 25 NEW job boards, then stop
./scripts/run_crawler.sh quick --discover 25

# Backward-compatible alias for --discover
./scripts/run_crawler.sh quick --limit 25
```

On Windows, use `start_comprehensive.bat` (CMD) or `./start_comprehensive.ps1` (PowerShell).

## Features

- **Multiple Search Engines**: DuckDuckGo (default) or Brave Search backend
- **Excel Output**: Exactly two `.xlsx` files per run (`*_companies.xlsx` and `*_aggregators.xlsx`)
- **Query Generation**: Broad set of job-board discovery queries (synonyms, regions, industries)
- **URL Extraction & Deduplication**: Automatically dedupes and normalizes links
- **Smart Filtering**: Heuristic-based job board identification
- **Content Verification**: Optional homepage scanning for job-related phrases
- **Targeted Discovery**: Stop automatically when a requested number of NEW job boards is found

## Usage Examples

```bash
# Discover up to 50 NEW job boards this run
python3 run.py --engine brave --filter --discover 50 --output output/standard_discovery

# Discover with content verification (slower)
python3 run.py --engine brave --filter --verify --discover 25 --output output/verified_discovery

# Multiple custom queries
python3 run.py --engine brave --filter --discover 30 \
    --queries "job boards" "remote job boards" "engineering job boards" \
    --output output/custom_discovery

# Resume from checkpoint and discover 20 more
python3 run.py --engine brave --filter --resume --discover 20 --output output/resumed_discovery
```

## Output Files

Each run writes only these two spreadsheets:

- `*_companies.xlsx` — Company career board results
- `*_aggregators.xlsx` — Job aggregator results

## CLI Options

- `--engine` – Search backend: `duckduckgo` (default) or `brave`
- `--queries` – Custom search queries (default: built-in set of 17+ queries)
- `--pages` – Result pages per query (default: 1)
- `--rate` – Delay between requests in seconds (default: 1.0)
- `--filter` – Keep only likely job board URLs
- `--verify` – Scan homepages for job keywords (slower)
- `--discover` – Stop when this many NEW job boards are discovered in this run
- `--limit` – Alias for `--discover` (backward compatibility)
- `--detect-careers` – Try common career-page paths for company domains
- `--resume` – Continue from prior checkpoint
- `--checkpoint` – Custom checkpoint path
- `--output` – Base output prefix (creates `*_companies.xlsx` and `*_aggregators.xlsx`)

## Configuration Notes

- **DuckDuckGo** often blocks automated requests with CAPTCHAs
- **Brave Search** is much more tolerant – use `--engine brave` for reliability
- Rate limiting is applied between requests (default 1 second)
- Heuristic filtering uses keywords: job, jobs, careers, work, hiring, apply, recruit, employment

## Project Structure

```
├── crawler.py              # Core crawler + heuristics
├── run.py                  # CLI wrapper
├── headless_crawler.py     # Playwright-based alternative
├── requirements.txt        # Dependencies
├── README.md              # This file
└── GITHUB_SETUP.md        # GitHub push instructions
```

## Dependencies

- `requests` – HTTP requests
- `beautifulsoup4` – HTML parsing
- `openpyxl` – Excel file generation
- `tqdm` – Progress bars (optional)

## GitHub Setup

To push this project to GitHub, see [GITHUB_SETUP.md](GITHUB_SETUP.md)

## Notes

- Uses lightweight HTML endpoints to minimize JS rendering
- Respects rate limits and uses normal browser user-agents
- All output files are excluded from git
