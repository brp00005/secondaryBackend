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
        "--discover",
        type=int,
        default=None,
        help="Stop when this many NEW job boards are discovered in this run",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Alias for --discover (backward compatible)",
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
    p.add_argument(
        "--chambers",
        action="store_true",
        help="Run Chamber-of-Commerce directory discovery (state -> chamber -> members)",
    )
    p.add_argument(
        "--states",
        nargs="+",
        help="List of states to search (e.g. 'California Texas'). If omitted, uses all US states",
    )
    p.add_argument(
        "--chamber-output",
        default="chambers.xlsx",
        help="Output workbook for chamber/member scraping",
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
    discover_target = args.discover if args.discover is not None else args.limit
    if discover_target is not None and discover_target <= 0:
        raise SystemExit("--discover/--limit must be greater than 0")
    
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
    seen_keys = set(checkpoint.get("discovered_keys", [])) if args.resume else set()
    if args.resume and not seen_keys:
        previous_count = checkpoint.get("discovered_count", 0)
        if previous_count:
            print(f"[Resume] Previous discovered count found ({previous_count}) but no key history; counting new discoveries from this run.")
    newly_discovered_urls: List[str] = []
    
    # Chambers workflow
    if args.chambers:
        print("Running Chamber-of-Commerce directory discovery...")
        states = args.states or [
            "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
            "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
            "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
            "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
            "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
            "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma",
            "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
            "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
            "West Virginia", "Wisconsin", "Wyoming",
        ]

        chamber_progress = checkpoint.get("chamber_progress", {})
        members_rows = []
        verified_rows = []

        for state in states:
            print(f"State: {state}")
            query = f"{state} chamber of commerce member directory"
            try:
                results = crawler.search(query, pages=1)
            except Exception as e:
                print(f"  Search error for {state}: {e}")
                continue

            chamber_sites = []
            for r in results:
                u = r.get("url")
                if not u:
                    continue
                d = crawler.get_domain(u)
                if not d:
                    continue
                if "chamber" in d or "chamber" in u.lower():
                    chamber_sites.append(u)

            chamber_sites = crawler.dedupe(chamber_sites)[:10]

            for site in chamber_sites:
                if chamber_progress.get(site):
                    print(f"  Skipping already-processed chamber: {site}")
                    continue
                print(f"  Inspecting chamber site: {site}")
                directory = crawler.find_member_directory(site)
                if not directory:
                    print("    No member directory found")
                    chamber_progress[site] = True
                    checkpoint["chamber_progress"] = chamber_progress
                    DuckDuckGoJobBoardCrawler.save_checkpoint(checkpoint, args.checkpoint)
                    continue

                print(f"    Found directory: {directory} — scraping members...")
                members = crawler.scrape_member_directory(directory, max_pages=50)
                print(f"    Extracted {len(members)} members")

                for m in members:
                    name = m.get("name")
                    url = m.get("url")
                    members_rows.append((state, site, name, url))

                    # quick company site check
                    if not crawler.confirm_company_site(url, deep=bool(args.verify)):
                        continue

                    # try to find career links and (optionally) verify
                    career_candidates = crawler.find_career_links(url)
                    found_career = None
                    if career_candidates:
                        if bool(args.verify):
                            for cand in career_candidates:
                                if crawler.verify_jobs_on_page(cand):
                                    found_career = cand
                                    break
                        else:
                            # quick mode: record the first candidate without deep fetch
                            found_career = career_candidates[0]

                    if found_career:
                        domain = crawler.get_domain(url)
                        verified_rows.append((state, site, name, url, domain, found_career))
                        # register discovery key to avoid duplicates later
                        seen_keys.add(domain or url)

                # mark chamber processed and save checkpoint
                chamber_progress[site] = True
                checkpoint["chamber_progress"] = chamber_progress
                checkpoint["discovered_keys"] = list(seen_keys)
                checkpoint["discovered_count"] = len(seen_keys)
                DuckDuckGoJobBoardCrawler.save_checkpoint(checkpoint, args.checkpoint)

        # save to workbook
        try:
            from openpyxl import Workbook
            wb = Workbook()
            ws1 = wb.active
            ws1.title = "Members"
            ws1.append(["State", "Chamber Site", "Member Name", "Member URL"])
            for r in members_rows:
                ws1.append(list(r))

            ws2 = wb.create_sheet("Verified Careers")
            ws2.append(["State", "Chamber Site", "Company Name", "Company URL", "Domain", "Career Page"])
            for r in verified_rows:
                ws2.append(list(r))

            wb.save(args.chamber_output)
            print(f"Saved chamber scraping results to {args.chamber_output}")
        except Exception as e:
            print(f"Error saving chamber workbook: {e}")

        # update checkpoint
        checkpoint["last_query_index"] = checkpoint.get("last_query_index", -1)
        checkpoint["discovered_keys"] = list(seen_keys)
        checkpoint["discovered_count"] = len(seen_keys)
        DuckDuckGoJobBoardCrawler.save_checkpoint(checkpoint, args.checkpoint)

        print("Chamber-of-Commerce run complete.")
        return
    # run queries
    for idx, q in enumerate(queries[start_index:], start=start_index):
        if discover_target and len(newly_discovered_urls) >= discover_target:
            print(f"[Target reached] Discovered {len(newly_discovered_urls)} new job boards")
            break
        
        print(f"[{idx + 1}/{len(queries)}] Searching: {q}")
        try:
            items = crawler.search(q, pages=args.pages)
            urls = crawler.extract_links(items)
            urls = crawler.dedupe(urls)

            if args.filter:
                urls = crawler.filter_urls(urls, verify_content=args.verify)

            new_for_query = 0
            for url in urls:
                domain = crawler.get_domain(url)
                unique_key = domain or url
                if unique_key in seen_keys:
                    continue
                seen_keys.add(unique_key)
                newly_discovered_urls.append(url)
                new_for_query += 1
                if discover_target and len(newly_discovered_urls) >= discover_target:
                    break

            print(f"  New discovered in query: {new_for_query} (total new: {len(newly_discovered_urls)})")
            
            # save checkpoint
            checkpoint["last_query_index"] = idx
            checkpoint["discovered_count"] = len(seen_keys)
            checkpoint["discovered_keys"] = list(seen_keys)
            DuckDuckGoJobBoardCrawler.save_checkpoint(checkpoint, args.checkpoint)

            if discover_target and len(newly_discovered_urls) >= discover_target:
                print(f"[Target reached] Discovered {len(newly_discovered_urls)} new job boards")
                break
        except KeyboardInterrupt:
            print("\n[Checkpoint saved] Run with --resume to continue from here")
            checkpoint["last_query_index"] = idx - 1
            checkpoint["discovered_count"] = len(seen_keys)
            checkpoint["discovered_keys"] = list(seen_keys)
            DuckDuckGoJobBoardCrawler.save_checkpoint(checkpoint, args.checkpoint)
            return
        except Exception as e:
            print(f"  Error: {e}")

    urls = newly_discovered_urls
    print(f"Discovered {len(urls)} new unique job board URLs in this run")
    
    # categorize
    print("Categorizing URLs...")
    categorized = categorize_urls(crawler, urls)
    aggregators = categorized["aggregators"]
    companies = categorized["companies"]
    
    print(f"  Aggregators: {len(aggregators)}")
    print(f"  Company career pages (candidates): {len(companies)}")

    # First ensure non-aggregator candidates are actually company websites.
    # Use deep check when --verify is requested.
    company_candidates = []
    for c in companies:
        domain = c.get("domain")
        check_url = c.get("url")
        is_company = crawler.confirm_company_site(check_url, deep=bool(args.verify))
        if not is_company:
            print(f"  Skipping non-company domain: {domain} ({check_url})")
            continue
        company_candidates.append(c)

    # detect career pages for the filtered company candidates if requested
    if args.detect_careers:
        print("Detecting career pages...")
        for company in company_candidates:
            domain = company["domain"]
            print(f"  Checking {domain} for career page...")
            career_page = crawler.find_career_page(domain)
            if career_page:
                company["career_page"] = career_page
                print(f"    Found: {career_page}")

    # Validate that company rows are actual job boards. If --verify was
    # requested we perform a deeper scrape; otherwise use lightweight check.
    validated_companies = []
    for c in company_candidates:
        check_url = c.get("career_page") or c.get("url")
        is_board = crawler.confirm_job_board(check_url, deep=bool(args.verify))
        if is_board:
            validated_companies.append(c)
        else:
            print(f"  Skipping non-job-board: {c.get('domain')} ({check_url})")
    companies = validated_companies
    
    # determine output paths
    base_output = Path(args.output)
    if base_output.suffix:
        base_name = str(base_output.parent / base_output.stem)
    else:
        base_name = str(base_output)
    
    company_file = f"{base_name}_companies.xlsx"
    aggregator_file = f"{base_name}_aggregators.xlsx"
    
    # save to spreadsheets (always exactly two output files)
    crawler.save_company_careers_to_excel(companies, company_file)
    print(f"Saved {len(companies)} company career pages to {company_file}")

    crawler.save_aggregators_to_excel(aggregators, aggregator_file)
    print(f"Saved {len(aggregators)} job aggregators to {aggregator_file}")
    
    # update checkpoint
    checkpoint["last_query_index"] = len(queries) - 1
    checkpoint["discovered_count"] = len(seen_keys)
    checkpoint["discovered_keys"] = list(seen_keys)
    DuckDuckGoJobBoardCrawler.save_checkpoint(checkpoint, args.checkpoint)

    print(f"\n✓ Crawl complete! ({len(urls)} new job boards discovered in this run)")


if __name__ == "__main__":
    main()
