#!/usr/bin/env python3
"""Scrape the Colorado chambers page and export unique chamber names + sites.

Writes results to `output/colorado_chambers.xlsx`.
"""
import logging
import re
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

URL = "https://www.officialusa.com/stateguides/chambers/colorado.html"
OUTPUT = "output/colorado_chambers.xlsx"


def fetch(url: str) -> str:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.text


def normalize_site(s: str, base: str) -> str:
    s = s.strip()
    if not s:
        return ''
    if s.startswith('http://') or s.startswith('https://'):
        return s
    if re.match(r'^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', s):
        return 'https://' + s
    if s.startswith('//'):
        return 'https:' + s
    return urljoin(base, s)


def extract_colorado(html: str, base: str) -> list:
    soup = BeautifulSoup(html, 'html.parser')
    seen = {}
    results = []

    # Primary: ul.list-unstyled lists
    for ul in soup.find_all('ul', class_='list-unstyled'):
        for li in ul.find_all('li'):
            raw = li.get_text(' ', strip=True)
            if not raw:
                continue
            name = re.sub(r'^[\u2022\-\*\+\s]+', '', raw).strip()
            name = re.split(r'\b(Website:|Phone:|Address:|Region:|Area:)', name)[0].strip()
            if not name:
                continue
            key = re.sub(r'[^A-Za-z0-9 ]+', '', name).lower().strip()
            if key in seen:
                continue
            # try to find a link
            site = ''
            a = li.find('a', href=True)
            if a:
                site = normalize_site(a['href'].strip(), base)
            seen[key] = {'chamber_name': name, 'chamber_url': site, 'raw': raw}
            results.append(seen[key])

    # Secondary: anchors or blocks that mention Chamber
    for tag in soup.find_all(['a','p','div','td','h1','h2','h3','h4','strong']):
        raw = tag.get_text(' ', strip=True)
        if not raw:
            continue
        for line in re.split(r'\n|\r|\.|;|\u2022', raw):
            line = line.strip()
            if len(line) < 3:
                continue
            if re.search(r'\bChamber\b|Chamber of Commerce', line, re.I):
                name = re.split(r'\b(Website:|Phone:|Address:|Region:|Area:)', line)[0].strip()
                key = re.sub(r'[^A-Za-z0-9 ]+', '', name).lower().strip()
                if not key or key in seen:
                    continue
                site = ''
                a = None
                try:
                    a = tag.find('a', href=True)
                except Exception:
                    a = None
                if a:
                    site = normalize_site(a['href'].strip(), base)
                seen[key] = {'chamber_name': name, 'chamber_url': site, 'raw': raw}
                results.append(seen[key])

    return results


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    html = fetch(URL)
    items = extract_colorado(html, URL)
    logging.info('Found %d raw chamber-like entries', len(items))
    df = pd.DataFrame(items)
    if not df.empty:
        df['key'] = df['chamber_name'].apply(lambda s: re.sub(r'[^A-Za-z0-9 ]+', '', str(s)).lower().strip())
        df = df.drop_duplicates(subset=['key'])
        df = df.drop(columns=['key'])
    logging.info('Writing %d unique chamber entries', len(df))
    df.to_excel(OUTPUT, index=False)
    print('Wrote', OUTPUT)


if __name__ == '__main__':
    main()
