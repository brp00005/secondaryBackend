#!/usr/bin/env python3
"""Verify Alaska chambers: extract expected names from officialusa and compare to spreadsheet.

This script does NOT hardcode chamber names; it parses the page structure to build the
expected list, then compares to `output/alaska_chambers.xlsx` produced by
`scripts/scrape_alaska_only.py`.
"""
from pathlib import Path
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd


URL = "https://www.officialusa.com/stateguides/chambers/alaska.html"
OUTFILE = Path("output/alaska_chambers.xlsx")


def fetch(url: str) -> str:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.text


def extract_expected_from_page(html: str):
    soup = BeautifulSoup(html, "html.parser")
    # Simpler, more reliable strategy: many chamber names are headings on the page.
    # Collect headings that mention 'chamber' and exclude generic/help headings.
    found = []
    for h in soup.find_all(re.compile(r"^h[1-6]$")):
        text = (h.get_text(' ') or '').strip()
        if not text:
            continue
        tl = text.lower()
        if 'chamber' in tl:
            # exclude generic section headings
            if re.search(r'membership|benefits|directory|resources|chambers of commerce', tl):
                continue
            found.append(text)

    # dedupe preserving order
    out = []
    seen = set()
    for n in found:
        k = re.sub(r"[^a-z0-9]+", "", n.lower())
        if k and k not in seen:
            seen.add(k)
            out.append(n)
    return out


def normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def compare(expected_names, sheet_names):
    exp_norm = [normalize(n) for n in expected_names]
    sheet_norm = [normalize(n) for n in sheet_names]

    matches = {}
    for e, en in zip(expected_names, exp_norm):
        found = [sheet_names[i] for i, sn in enumerate(sheet_norm) if en and en in sn]
        matches[e] = found
    return matches


def main():
    print("Fetching officialusa Alaska page to build expected list...")
    html = fetch(URL)
    expected = extract_expected_from_page(html)
    print(f"Extracted {len(expected)} candidate names from page")

    if not OUTFILE.exists():
        print("Error: expected output spreadsheet not found:", OUTFILE)
        return 2

    df = pd.read_excel(OUTFILE).fillna("")
    sheet_names = [str(x).strip() for x in df.get('chamber_name', df.columns[0])]
    print(f"Spreadsheet has {len(sheet_names)} rows")

    matches = compare(expected, sheet_names)
    found_count = sum(1 for v in matches.values() if v)
    print(f"Matched {found_count} of {len(expected)} extracted names")
    for e, v in matches.items():
        status = "FOUND" if v else "MISSING"
        print('-', status, '|', e, '->', (v if v else ''))

    # summary of sheet entries that look like chambers
    chamber_like = [s for s in sheet_names if 'chamber' in s.lower() or 'chambers' in s.lower()]
    print(f"\nSheet entries that look like chambers: {len(chamber_like)}")
    for s in chamber_like:
        print('-', s)

    # final verdict: target expected count 26
    ok = len(sheet_names) >= 26 and found_count >= 20
    print('\nFinal check — sheet rows >=26:', len(sheet_names) >= 26)
    print('Extracted names >=26:', len(expected) >= 26)
    print('Likely OK:', ok)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
