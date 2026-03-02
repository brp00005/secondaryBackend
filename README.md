# DuckDuckGo Job Board Crawler

Simple Python scraper that queries DuckDuckGo (HTML endpoint) to discover job boards and collect result links.

Quick start

1. Create a virtualenv and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the crawler (example):

```bash
python run.py --queries "job board" "careers site" --pages 2 --output results.json
```

Notes
- Uses the DuckDuckGo HTML endpoint (`https://html.duckduckgo.com/html/`) to avoid heavy JS.
- Be polite: configurable rate limit and user-agent, plus optional delays.

Features
- Generates a broad set of job-board discovery queries (synonyms, regions,
  industries).
- Pluggable search engine backends; supports **DuckDuckGo** and **Brave Search**
  (choose via `--engine`).
- Extracts outbound links from SERPs and deduplicates them automatically.
- Heuristic filtering to identify likely job board domains.
- Optional content verification by scanning the homepage for job-related text.
- CLI flags for outputting either raw results, filtered URLs, or simple domain
  lists.

The default engine is DuckDuckGo, but Brave Search tends to block bots much
less aggressively – try `--engine brave` if you run into CAPTCHAs.

Usage examples

```bash
# basic run, collecting raw result links:
python run.py --queries "job board" "careers site" \
    --pages 2 --output results.json

# run with filtering and homepage verification:
python run.py --filter --verify --output filtered.json

# output only unique domains, useful for feeding into another pipeline:
python run.py --filter --domains --output domains.txt
```

Files
- `crawler.py` — crawler and heuristics implementation
- `run.py` — CLI wrapper offering query generation and filtering flags
- `requirements.txt` — pip deps
