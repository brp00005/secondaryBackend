#!/bin/bash
# One-command starter for comprehensive job board crawl (moved to scripts/)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

if [ ! -x "$SCRIPT_DIR/run_crawler.sh" ]; then
    chmod +x "$SCRIPT_DIR/run_crawler.sh"
fi

exec "$SCRIPT_DIR/run_crawler.sh" extensive --engine brave --pages 2 --rate 1.0
