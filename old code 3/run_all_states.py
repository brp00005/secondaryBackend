#!/usr/bin/env python3
"""Orchestrate extraction for all snapshot state pages (excluding CO/AK).

Reads `site_html/*.html`, runs `extractors.extract_state`, writes `output/<state>_chambers.xlsx`.
Also writes a simple report printing counts and expected counts from snapshots.
"""
import glob
import sys
from pathlib import Path
# ensure local scripts folder is on sys.path so we can import modules by name
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import extractors
import helpers

BASE = 'https://www.officialusa.com/stateguides/chambers/'
SNAP_DIR = Path('site_html')
OUT_DIR = Path('output')
OUT_DIR.mkdir(exist_ok=True)

SKIP = {'colorado.html', 'alaska.html', 'vermont.html'}


def run():
    report = []
    for path in sorted(SNAP_DIR.glob('*.html')):
        name = path.name
        if name in SKIP:
            continue
        state = name.replace('.html', '')
        html = path.read_text(encoding='utf-8', errors='ignore')
        items = extractors.extract_state(name, html, BASE + name)
        outpath = OUT_DIR / f'{state}_chambers.xlsx'
        # try extract summary if available
        summary = None
        try:
            expected = helpers.extract_expected_from_snapshot(html)
        except Exception:
            expected = []
        helpers.write_workbook(items, str(outpath), summary)
        report.append((state, len(expected), len(items), str(outpath)))
        print(f'Wrote {outpath} — snapshot-expected={len(expected)} extracted={len(items)}')

    print('\nSummary:')
    for state, expect, found, out in report:
        status = 'OK' if expect == found else 'MISMATCH'
        print(f'{state}: expected={expect} extracted={found} {status} -> {out}')


if __name__ == '__main__':
    run()
