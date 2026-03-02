#!/usr/bin/env python3
"""CLI wrapper for the DuckDuckGo job board crawler."""
import argparse
from pathlib import Path
from typing import List

from crawler import DuckDuckGoJobBoardCrawler


def parse_args():
    p = argparse.ArgumentParser(description="DuckDuckGo job board crawler")
    p.add_argument("--queries", nargs="+", help="Search queries to run", required=False)
    p.add_argument("--pages", type=int, default=1, help="Pages per query")
    p.add_argument("--rate", type=float, default=1.0, help="Seconds between requests")
    p.add_argument("--output", default="results.json", help="Output JSON file")
    p.add_argument(
        "--engine",
        choices=["duckduckgo", "brave"],
        default="duckduckgo",
        help="Which search engine backend to use",
    )
    p.add_argument(
        "--filter",
        action="store_true",
        help="Keep only URLs that match job-board heuristics",
    )
    p.add_argument(
        "--verify",
        action="store_true",
        help="When filtering, fetch each homepage and scan for job keywords",
    )
    p.add_argument(
        "--domains",
        action="store_true",
        help="Write only the unique domains to the output file",
    )
    return p.parse_args()


def main():
    args = parse_args()
    queries: List[str] = args.queries or [
        "job board",
        "jobs board",
        "job listings",
        "careers site",
    ]

    crawler = DuckDuckGoJobBoardCrawler(rate_limit=args.rate, engine=args.engine)
    all_items = []
    for q in queries:
        print(f"Searching: {q}")
        items = crawler.search(q, pages=args.pages)
        for it in items:
            it.setdefault("query", q)
        all_items.extend(items)

    # extract urls and dedupe
    urls = crawler.extract_links(all_items)
    urls = crawler.dedupe(urls)
    print(f"extracted {len(urls)} unique urls")

    if args.filter:
        urls = crawler.filter_urls(urls, verify_content=args.verify)
        print(f"{len(urls)} urls after filtering")

    if args.domains:
        domains = sorted({crawler.get_domain(u) for u in urls if crawler.get_domain(u)})
        # when writing domains we just dump a simple list of strings
        if args.output.endswith('.xlsx'):
            crawler.save_domains_to_excel(domains, args.output)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                for d in domains:
                    f.write(d + "\n")
        print(f"saved {len(domains)} unique domains to {args.output}")
    else:
        # default behaviour: save url list as json or excel
        to_save = [{\"url\": u} for u in urls]
        if args.output.endswith('.xlsx'):
            crawler.save_results_to_excel(to_save, args.output)
        else:
            crawler.save(to_save, args.output)
        print(f"saved {len(to_save)} items to {args.output}")


if __name__ == "__main__":
    main()
