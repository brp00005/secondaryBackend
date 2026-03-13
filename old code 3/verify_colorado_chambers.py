#!/usr/bin/env python3
"""Verify Colorado chambers: extract expected entries from officialusa and compare to spreadsheet.

This does not hardcode names; it parses the page structure (lists, headings, anchors)
to build the expected set, then compares to `output/colorado_chambers.xlsx`.
"""
from pathlib import Path
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd

URL = "https://www.officialusa.com/stateguides/chambers/colorado.html"
OUTFILE = Path("output/colorado_chambers.xlsx")


def fetch(url: str) -> str:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.text


def extract_expected(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    found = []
    # 1) list items in list-unstyled
    for ul in soup.find_all('ul', class_='list-unstyled'):
        for li in ul.find_all('li'):
            txt = (li.get_text(' ', strip=True) or '').strip()
            if txt:
                # split off Website/Phone/Address
                name = re.split(r'\b(Website:|Phone:|Address:|Region:|Area:)', txt)[0].strip()
                if name:
                    found.append(name)

    # 2) headings followed by lists/anchors
    for h in soup.find_all(re.compile(r'^h[1-6]$')):
        txt = (h.get_text(' ', strip=True) or '').strip()
        if not txt:
            continue
        cur = h.next_sibling
        steps = 0
        while cur and steps < 60:
            if getattr(cur, 'name', None) and re.match(r'^h[1-6]$', cur.name):
                break
            if hasattr(cur, 'find_all'):
                for a in cur.find_all('a', href=True):
                    atext = (a.get_text(' ', strip=True) or '').strip()
                    if atext:
                        found.append(atext)
                for li in cur.find_all('li'):
                    ltxt = (li.get_text(' ', strip=True) or '').strip()
                    if ltxt:
                        name = re.split(r'\b(Website:|Phone:|Address:|Region:|Area:)', ltxt)[0].strip()
                        found.append(name)
            cur = cur.next_sibling
            steps += 1

    # 3) any anchor which text contains 'Chamber'
    for a in soup.find_all('a', href=True):
        text = (a.get_text(' ', strip=True) or '').strip()
        if not text:
            continue
        if 'chamber' in text.lower():
            found.append(text)

    # dedupe preserving order
    out = []
    seen = set()
    for n in found:
        key = re.sub(r'[^a-z0-9]+', '', n.lower())
        if key and key not in seen:
            seen.add(key)
            out.append(n)
    return out


def normalize(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', (s or '').lower())


def compare(expected, sheet):
    exp_norm = {normalize(e): e for e in expected}
    sheet_norm = {normalize(s): s for s in sheet}
    matched = {}
    for k, e in exp_norm.items():
        # find any sheet key that contains exp key or vice versa
        found = [v for sk, v in sheet_norm.items() if k and (k in sk or sk in k)]
        matched[e] = found
    return matched


def main():
    print('Fetching Colorado page to build expected list...')
    html = fetch(URL)
    expected = extract_expected(html)
    print(f'Extracted {len(expected)} candidate entities from page')

    if not OUTFILE.exists():
        print('Error: output spreadsheet not found:', OUTFILE)
        return 2
    df = pd.read_excel(OUTFILE).fillna('')
    sheet_names = [str(x).strip() for x in df.get('chamber_name', df.columns[0])]
    print(f'Spreadsheet has {len(sheet_names)} rows')

    matches = compare(expected, sheet_names)
    found_count = sum(1 for v in matches.values() if v)
    print(f'Matched {found_count} of {len(expected)} extracted candidates')
    for e, v in matches.items():
        status = 'FOUND' if v else 'MISSING'
        print('-', status, '|', e, '->', (v if v else ''))

    # summary
    chamber_like = [s for s in sheet_names if 'chamber' in s.lower()]
    print('\nSheet entries that look like chambers:', len(chamber_like))
    for s in chamber_like[:200]:
        print('-', s)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
