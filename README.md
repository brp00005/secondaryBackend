# DuckDuckGo Job Board Crawler

Simple Python scraper that queries search engines to discover job boards and collect result links. Supports output to **Excel (.xlsx)**, JSON, and text formats.

## Quick Start

1. Create a virtualenv and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the crawler:

```bash
# Save filtered job board domains to Excel
python3 run.py --engine brave --filter --domains --output job_boards.xlsx

# Save full results to Excel
python3 run.py --engine brave --filter --output results.xlsx

# Traditional text output
python3 run.py --engine brave --filter --domains --output job_boards.txt
```

## Features

- **Multiple Search Engines**: DuckDuckGo (default) or Brave Search backend
- **Excel Output**: Automatically formatted `.xlsx` files with column headers
- **Query Generation**: Broad set of job-board discovery queries (synonyms, regions, industries)
- **URL Extraction & Deduplication**: Automatically dedupes and normalizes links
- **Smart Filtering**: Heuristic-based job board identification
- **Content Verification**: Optional homepage scanning for job-related phrases
- **Flexible Output**: JSON, Excel, or text formats

## Usage Examples

```bash
# Excel output with domain filtering
python3 run.py --engine brave --filter --domains --output job_boards.xlsx

# Full results with content verification (slower but more accurate)
python3 run.py --engine brave --filter --verify --output verified_boards.xlsx

# Multiple custom queries
python3 run.py --engine brave --filter --domains \
    --queries "job boards" "remote jobs" "startup careers" \
    --output results.xlsx

# Raw results without filtering
python3 run.py --engine brave --output all_results.xlsx

# Text output for scripting
python3 run.py --engine brave --filter --domains --output domains.txt
```

## Output Formats

### Excel with Domains
When using `--domains --output file.xlsx`:
```
Domain                  | URL
------------------------|----
www.indeed.com          | https://www.indeed.com
www.glassdoor.com       | https://www.glassdoor.com
www.ziprecruiter.com    | https://www.ziprecruiter.com
```

### Excel with Full Results
When using `--output file.xlsx` (without `--domains`):
```
Title                      | URL                        | Query
---------------------------|---------------------------|--------
Job Search - Indeed        | https://www.indeed.com/   | job boards
Glassdoor Jobs             | https://www.glassdoor.com | job boards
```

## CLI Options

- `--engine` – Search backend: `duckduckgo` (default) or `brave`
- `--queries` – Custom search queries (default: built-in set of 17+ queries)
- `--pages` – Result pages per query (default: 1)
- `--rate` – Delay between requests in seconds (default: 1.0)
- `--filter` – Keep only likely job board URLs
- `--verify` – Scan homepages for job keywords (slower)
- `--domains` – Output only domain names
- `--output` – Output file path (`.json`, `.xlsx`, or `.txt`)

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
