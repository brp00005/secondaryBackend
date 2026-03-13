#!/usr/bin/env python3
"""Small CLI to print proxy health/stats written by the crawler."""
import argparse
import json
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Print proxy health/stats from JSON file")
    p.add_argument("--stats", help="Path to proxy stats JSON file", default="proxy_stats.json")
    return p.parse_args()


def main():
    args = parse_args()
    p = Path(args.stats)
    if not p.exists():
        print(f"No stats file at {p}; run crawler with --proxy-stats-file to generate one.")
        return
    try:
        data = json.loads(p.read_text())
    except Exception as e:
        print(f"Error reading stats file: {e}")
        return

    rows = []
    for proxy, stats in data.items():
        attempts = stats.get("attempts", 0)
        successes = stats.get("successes", 0)
        failures = stats.get("failures", 0)
        banned = stats.get("banned_until")
        rows.append((proxy, attempts, successes, failures, banned))

    # sort by failures desc
    rows.sort(key=lambda r: r[3], reverse=True)

    print(f"Proxy Health ({len(rows)} proxies)")
    print("{:<40} {:>8} {:>9} {:>9} {:>20}".format("Proxy", "Attempts", "Success", "Failures", "BannedUntil"))
    for r in rows:
        print("{:<40} {:>8} {:>9} {:>9} {:>20}".format(r[0], r[1], r[2], r[3], str(r[4] or "-")))


if __name__ == "__main__":
    main()
