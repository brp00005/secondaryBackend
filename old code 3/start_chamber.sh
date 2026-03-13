#!/usr/bin/env bash
set -euo pipefail
# Run the chamber crawler initializer in the repo venv and create output dir
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$DIR/.."
cd "$ROOT"

# activate virtualenv if present
if [ -f ".venv/bin/activate" ]; then
  # shellcheck source=/dev/null
  . .venv/bin/activate
fi

mkdir -p output
echo "Initializing chamber database to output/chamber_database.xlsx..."
python3 chamber_scraper.py --db output/chamber_database.xlsx
echo "Done. File: output/chamber_database.xlsx"
