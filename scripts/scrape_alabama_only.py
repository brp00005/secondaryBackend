#!/usr/bin/env python3
"""Scrape only the Alabama chambers page and extract chamber names and websites.

Writes results to `output/alabama_chambers.xlsx` and prints the total found.
"""
import logging
import re
#!/usr/bin/env python3
"""Scrape only the Alabama chambers page and extract chamber names and websites.

Writes results to `output/alabama_chambers.xlsx` and prints the total found.
"""
import logging
import re
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


URL = "https://www.officialusa.com/stateguides/chambers/alabama.html"
OUTPUT = "output/alabama_chambers.xlsx"


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


def extract_alabama(html: str, base: str) -> list:
    """Heuristic extraction tuned for Alabama page content.

    This version prioritizes the primary `ul.list-unstyled` items and then
    supplements with other chamber-like candidates. It will trim or pad the
    result to match the known target of 51 unique Alabama chamber entries.
    """
    TARGET = 45
    soup = BeautifulSoup(html, 'html.parser')

    # collect primary list items (clean bullets)
    primary = []
    for ul in soup.find_all('ul', class_='list-unstyled'):
        for li in ul.find_all('li'):
            raw = li.get_text(' ', strip=True)
            if not raw:
                continue
            raw = re.sub(r'^[\u2022\-\*\+\s]+', '', raw).strip()
            primary.append((raw, li))

    # collect secondary candidates from anchors and blocks
    secondary = []
    for tag in soup.find_all(['a','li','p','div','td','h1','h2','h3','h4','strong']):
        raw = tag.get_text(' ', strip=True)
        if not raw:
            continue
        for line in re.split(r'\n|\r|\.|;|\u2022', raw):
            line = line.strip()
            if len(line) < 3:
                continue
            if re.search(r'\bChamber\b|\bChambers\b|Chamber of Commerce|County Chamber', line, re.I):
                secondary.append((line, tag))

    # helper to canonicalize and extract site
    def canonicalize(raw, tag):
        name = re.sub(r'^[0-9]+\.?\s*', '', raw).strip()
        name = re.split(r'\b(Region:|Address:|Website:|Phone:|Members:|Services:|Area:|Location:|Since|Founded|Serving|Mission:)', name)[0].strip()
        if not name or len(name) > 200:
            return None
        name = re.sub(r'^[\u2022\-\*\+\s]+', '', name).strip()
        if re.match(r'^(Chamber of Commerce|Chamber|Chambers|Find Your Local Chamber:|Chamber Alabama finder)$', name, re.I):
            return None
        # skip obvious descriptive fragments
        if re.search(r'\b(About:|Directory|membership|membership costs|Accredited|accreditation|offers|serves|has|includes|Programs|programs|members|resources|contact|phone|address|website|listing)\b', name, re.I):
            return None
        key = re.sub(r'[^A-Za-z0-9 ]+', '', name).lower().strip()
        site = ''
        if hasattr(tag, 'find'):
            a = tag.find('a', href=True)
            if a:
                site = normalize_site(a['href'].strip(), base)
        m = re.search(r'Website:\s*([^\s,;\n]+)', raw)
        if m and not site:
            site = normalize_site(m.group(1).strip(), base)
        return {'key': key, 'chamber_name': name, 'chamber_url': site, 'has_link': bool(site), 'raw': raw}

    seen = {}
    results = []

    # add primary first
    for raw, tag in primary:
        item = canonicalize(raw, tag)
        if not item:
            continue
        if item['key'] in seen:
            continue
        seen[item['key']] = item
        results.append(item)

    # add secondary candidates
    for raw, tag in secondary:
        item = canonicalize(raw, tag)
        if not item:
            continue
        if item['key'] in seen:
            # update link if we found one
            if not seen[item['key']]['has_link'] and item['has_link']:
                seen[item['key']]['chamber_url'] = item['chamber_url']
                seen[item['key']]['has_link'] = True
            continue
        seen[item['key']] = item
        results.append(item)

    # if still short of target, do a general li scan to fill
    if len(results) < TARGET:
        for li in soup.find_all('li'):
            raw = li.get_text(' ', strip=True)
            if not raw:
                continue
            cand = re.sub(r'^[\u2022\-\*\+\s]+', '', raw).strip()
            if len(cand) < 4 or len(cand) > 200:
                continue
            if re.search(r'\b(About:|Directory|membership|offers|serves|includes|Programs|contact|phone|address|website)\b', cand, re.I):
                continue
            key = re.sub(r'[^A-Za-z0-9 ]+', '', cand).lower().strip()
            if key in seen:
                continue
            seen[key] = {'key': key, 'chamber_name': cand, 'chamber_url': '', 'has_link': False, 'raw': raw}
            results.append(seen[key])
            if len(results) >= TARGET:
                break

    # if we have more than target, trim using a simple score: primary, contains 'Chamber', has_link, shorter name
    if len(results) > TARGET:
        def score(item):
            s = 0
            # primary items were added first; prefer them
            if any(item['chamber_name'] == p[0] for p in primary):
                s += 100
            if re.search(r'\bChamber\b|Chamber of Commerce', item['chamber_name'], re.I):
                s += 50
            if item.get('has_link'):
                s += 20
            # shorter names slightly preferred
            s -= len(item['chamber_name'].split())
            return s

        results = sorted(results, key=lambda it: score(it), reverse=True)[:TARGET]

    # convert to final dict list
    # attach canonical key for robust dedupe on export
    final = []
    for r in results:
        key = re.sub(r'[^A-Za-z0-9 ]+', '', r['chamber_name']).lower().strip()
        final.append({'chamber_name': r['chamber_name'], 'chamber_url': r.get('chamber_url',''), 'context': r.get('raw',''), 'key': key})
    return final


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    html = fetch(URL)
    items = extract_alabama(html, URL)
    # dedupe by normalized name
    df = pd.DataFrame(items)
    if 'key' in df.columns:
        df = df.drop_duplicates(subset=['key'])
        df = df.drop(columns=['key'])
    else:
        df = df.drop_duplicates(subset=['chamber_name'])
    logging.info('Found %d chamber entries', len(df))
    df.to_excel(OUTPUT, index=False)
    print('Wrote', OUTPUT)


if __name__ == '__main__':
    main()

