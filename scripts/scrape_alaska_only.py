#!/usr/bin/env python3
"""Scrape only the Alaska chambers page and extract all chamber names and websites.

Writes results to `output/alaska_chambers.xlsx` and prints the total found.
"""
import logging
import re
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag, NavigableString


URL = "https://www.officialusa.com/stateguides/chambers/alaska.html"
OUTPUT = "output/alaska_chambers.xlsx"


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
    # sometimes it's like 'alaskachamber.com' or 'www.example.org'
    if re.match(r'^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', s):
        return 'https://' + s
    # if it's an href-like
    if s.startswith('//'):
        return 'https:' + s
    # fallback: join with base
    return urljoin(base, s)


def extract_alaska(html: str, base: str) -> list:
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    seen_names = set()

    def is_likely_name(s: str) -> bool:
        s = s.strip()
        if not s:
            return False
        if len(s) > 80:
            return False
        words = re.findall(r"[A-Za-z']+", s)
        if not words:
            return False
        cap = sum(1 for w in words if w[0].isupper())
        if cap / max(1, len(words)) < 0.3:
            return False
        # must contain 'Chamber'
        if 'Chamber' not in s:
            return False
        return True

    # iterate over probable blocks
    blocks = soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'p', 'li', 'div'])
    for tag in blocks:
        text = tag.get_text('\n', strip=True)
        if not text:
            continue
        # skip heading blocks that are section titles
        if re.search(r'^(Major Regional|Regional Chambers|Regional Chambers by Area|Statewide Founded)', text, re.I):
            continue
        # find candidate name if contains 'Chamber' (singular) or 'Chamber of'
        if not re.search(r'\bChamber\b', text):
            continue
        # avoid plural section headings
        if re.search(r'\bChambers\b', text) and len(text.split()) <= 4:
            continue

        # name is usually before 'Region:' or 'Website:' or 'About:'
        name_candidate = re.split(r'\bAbout:|\bRegion:|\bWebsite:|\bPhone:|\bAddress:', text)[0].strip()
        # remove leading numeric markers
        name_candidate = re.sub(r'^\d+\s*', '', name_candidate).strip()
        # trim common trailing descriptive keywords
        name_candidate = re.split(r"\b(Serving|Gateway|Focus:|Members:|Status:|Founded|Mission:|Largest|Supports|Providing|Phone:|Email:|Website:|Region:|Area:|Location:)", name_candidate)[0].strip()
        # further clean: drop long descriptive lines
        if len(name_candidate) > 140:
            # choose first line
            name_candidate = name_candidate.split('\n')[0].strip()
        # basic sanity: must be likely a name
        if not is_likely_name(name_candidate):
            continue
        # exclude generic sections
        generic_exclude = [
            'Chamber Membership Benefits', 'Chamber of Commerce Directory', 'What is the Alaska Native Chamber',
            'Chamber of Commerce', 'Chamber Membership Benefits in Alaska'
        ]
        if any(name_candidate.strip().lower().startswith(g.lower()) for g in generic_exclude):
            continue

        # find website: look for anchor inside tag
        site = ''
        a = tag.find('a', href=True)
        if a:
            site = a['href'].strip()
            site = normalize_site(site, base)
        else:
            # search for Website: pattern in this tag's text
            m = re.search(r'Website:\s*([^\s,;\n]+)', text)
            if m:
                site = normalize_site(m.group(1).strip(), base)
            else:
                # search following siblings for Website or anchor (up to 4 siblings)
                sib = tag.next_sibling
                steps = 0
                while sib and steps < 6:
                    if isinstance(sib, Tag):
                        stext = sib.get_text('\n', strip=True)
                        m2 = re.search(r'Website:\s*([^\s,;\n]+)', stext)
                        if m2:
                            site = normalize_site(m2.group(1).strip(), base)
                            break
                        a2 = sib.find('a')
                        if a2 and a2.has_attr('href'):
                            site = normalize_site(a2['href'].strip(), base)
                            break
                    elif isinstance(sib, NavigableString):
                        stext = str(sib).strip()
                        m2 = re.search(r'Website:\s*([^\s,;\n]+)', stext)
                        if m2:
                            site = normalize_site(m2.group(1).strip(), base)
                            break
                    sib = sib.next_sibling
                    steps += 1

        name = ' '.join(name_candidate.split())
        if not name:
            continue
        # exclude generic or duplicate entries
        if re.search(r'Directory|Organization|Membership|Benefits', name, re.I):
            continue
        if name.strip().lower().startswith('statewide'):
            continue
        if name.lower() in seen_names:
            # update site if missing
            for r in results:
                if r['chamber_name'].lower() == name.lower() and not r['chamber_url'] and site:
                    r['chamber_url'] = site
            continue
        seen_names.add(name.lower())
        results.append({'chamber_name': name, 'chamber_url': site, 'context': text})

    return results


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    html = fetch(URL)
    items = extract_alaska(html, URL)
    logging.info('Found %d chamber entries (raw)', len(items))
    df = pd.DataFrame(items)
    # canonical key for robust dedupe
    if not df.empty:
        df['key'] = df['chamber_name'].apply(lambda s: re.sub(r'[^A-Za-z0-9 ]+', '', str(s)).lower().strip())
        df = df.drop_duplicates(subset=['key'])
        df = df.drop(columns=['key'])
    logging.info('Writing %d unique chamber entries', len(df))
    df.to_excel(OUTPUT, index=False)
    print('Wrote', OUTPUT)


if __name__ == '__main__':
    main()
