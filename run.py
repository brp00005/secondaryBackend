#!/usr/bin/env python3
"""CLI wrapper for the DuckDuckGo job board crawler."""
import argparse
import json
from pathlib import Path
from typing import List, Dict

from crawler import DuckDuckGoJobBoardCrawler


def parse_args():
    p = argparse.ArgumentParser(description="DuckDuckGo job board crawler with resume support")
    p.add_argument("--queries", nargs="+", help="Search queries to run", required=False)
    p.add_argument("--pages", type=int, default=1, help="Pages per query")
    p.add_argument("--rate", type=float, default=1.0, help="Seconds between requests")
    p.add_argument("--output", default="results.json", help="Base output path (auto-suffixed)")
    p.add_argument(
        "--engine",
        choices=["duckduckgo", "brave"],
        default="brave",
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
        "--limit",
        type=int,
        default=None,
        help="Max number of job boards to discover (None = unlimited)",
    )
    p.add_argument(
        "--detect-careers",
        action="store_true",
        help="Attempt to find career pages for company domains",
    )
    p.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint if available",
    )
    p.add_argument(
        "--checkpoint",
        default=".crawler_checkpoint.json",
        help="Checkpoint file path",
    )
    return p.parse_args()


def categorize_urls(crawler, urls: List[str]) -> Dict[str, List[Dict]]:
    """Categorize URLs into aggregators and company career pages."""
    aggregators = []
    companies = []
    
    for url in urls:
        domain = crawler.get_domain(url)
        if not domain:
            continue
        
        if crawler.is_job_aggregator(url):
            aggregators.append({
                "url": url,
                "domain": domain,
                "title": domain,
            })
        else:
            companies.append({
                "url": url,
                "domain": domain,
                "title": domain,
                "career_page": url,
            })
    
    return {"aggregators": aggregators, "companies": companies}


def main():
    args = parse_args()
    
    # load checkpoint if resuming
    checkpoint = DuckDuckGoJobBoardCrawler.load_checkpoint(args.checkpoint)
    
    queries: List[str] = args.queries or DuckDuckGoJobBoardCrawler.default_queries()
    
    # resume from last query
    start_index = 0
    if args.resume:
        start_index = checkpoint.get("last_query_index", -1) + 1
        if start_index > 0:
            print(f"[Resume] Starting from query #{start_index} (discovered: {checkpoint.get('discovered_count', 0)})")
    
    crawler = DuckDuckGoJobBoardCrawler(rate_limit=args.rate, engine=args.engine)
    all_items = []
    discovered_count = checkpoint.get("discovered_count", 0) if args.resume else 0
    
    # run queries
    for idx, q in enumerate(queries[start_index:], start=start_index):
        if args.limit and discovered_count >= args.limit:
            print(f"[Limit reached] Discovered {discovered_count} job boards")
            break
        
        print(f"[{idx + 1}/{len(queries)}] Searching: {q}")
        try:
            items = crawler.search(q, pages=args.pages)
            for it in items:
                it.setdefault("query", q)
            all_items.extend(items)
            
            # save checkpoint
            checkpoint["last_query_index"] = idx
            DuckDuckGoJobBoardCrawler.save_checkpoint(checkpoint, args.checkpoint)
        except KeyboardInterrupt:
            print("\n[Checkpoint saved] Run with --resume to continue from here")
            checkpoint["last_query_index"] = idx - 1
            checkpoint["discovered_count"] = discovered_count
            DuckDuckGoJobBoardCrawler.save_checkpoint(checkpoint, args.checkpoint)
            return
        except Exception as e:
            print(f"  Error: {e}")
    
    # extract and dedupe
    urls = crawler.extract_links(all_items)
    urls = crawler.dedupe(urls)
    print(f"Extracted {len(urls)} unique URLs")
    
    if args.filter:
        urls = crawler.filter_urls(urls, verify_content=args.verify)
        print(f"{len(urls)} URLs after filtering")
    
    # apply limit
    if args.limit:
        urls = urls[:args.limit]
    
    discovered_count = len(urls)
    
    # categorize
    print("Categorizing URLs...")
    categorized = categorize_urls(crawler, urls)
    aggregators = categorized["aggregators"]
    companies = categorized["companies"]
    
    print(f"  Aggregators: {len(aggregators)}")
    print(f"  Company career pages: {len(companies)}")
    
    # detect career pages if requested
    if args.detect_careers:
        print("Detecting career pages...")
        for company in companies:
            if discovered_count >= (args.limit or float('inf')):
                break
            domain = company["domain"]
            print(f"  Checking {domain}...")
            career_page = crawler.find_career_page(domain)
            if career_page:
                company["career_page"] = career_page
                print(f"    Found: {career_page}")
    
    # determine output paths
    base_output = Path(args.output)
    if base_output.suffix:
        base_name = str(base_output.parent / base_output.stem)
    else:
        base_name = str(base_output)
    
    company_file = f"{base_name}_companies.xlsx"
    aggregator_file = f"{base_name}_aggregators.xlsx"
    
    # save to spreadsheets
    if companies:
        crawler.save_company_careers_to_excel(companies, company_file)
        print(f"Saved {len(companies)} company career pages to {company_file}")
    
    if aggregators:
        crawler.save_aggregators_to_excel(aggregators, aggregator_file)
        print(f"Saved {len(aggregators)} job aggregators to {aggregator_file}")
    
    # update checkpoint
    checkpoint["last_query_index"] = len(queries) - 1
    checkpoint["discovered_count"] = discovered_count
    DuckDuckGoJobBoardCrawler.save_checkpoint(checkpoint, args.checkpoint)
    
    print(f"\n✓ Crawl complete! ({discovered_count} job boards discovered)")


if __name__ == "__main__":
    main()
