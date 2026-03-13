#!/usr/bin/env python3
"""Crawl OfficialUSA Chambers state pages and save to an Excel file.

Usage:
    python scripts/crawl_officialusa.py
"""
import argparse
import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import pandas as pd


BASE_URL = "https://www.officialusa.com/stateguides/chambers/"


def fetch(url: str) -> str:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.text


def parse_state_links(html: str, base: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("/stateguides/chambers/") or \
           href.startswith(base) or \
           "/stateguides/chambers/" in href:
            full = urljoin(base, href)
            # filter out index or anchors
            if full.rstrip("/") == base.rstrip("/"):
                continue
            if full.endswith("/"):
                full = full[:-1]
            if full.lower().endswith(".html"):
                links.add(((a.get_text(strip=True) or full.split("/")[-1].replace('.html','')).strip(), full))
            else:
                # include non-.html if it contains the pattern
                links.add(((a.get_text(strip=True) or full), full))
    # normalize to list of dicts
    results = []
    seen_urls = set()
    for text, url in links:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        results.append({"state": text, "url": url})
    return results


DEFAULT_OUTPUT = "output/state_chambers.xlsx"


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.info("Fetching %s", BASE_URL)
    html = fetch(BASE_URL)
    logging.info("Parsing links")
    rows = parse_state_links(html, BASE_URL)
    if not rows:
        logging.error("No state links found")
        return

    df = pd.DataFrame(rows)
    logging.info("Writing %d rows to %s", len(df), DEFAULT_OUTPUT)
    df.to_excel(DEFAULT_OUTPUT, index=False)
    logging.info("Done")


if __name__ == "__main__":
    main()
