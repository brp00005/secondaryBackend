"""Generic extractors for state chamber pages.

This module exposes `extract_state(state_name, html, base)` which returns a list
of dicts with `chamber_name` and optional `chamber_url` fields.
"""
from bs4 import BeautifulSoup
import re
from typing import List, Dict
from helpers import normalize_site, dedupe_key
from state_rules import get_rules


# noisy substrings to skip when in conservative mode
_NOISE_PATTERNS = [
    r'Key Contacts', r'Chamber Focus Areas', r'What are the benefits', r'Visit Website',
    r'Chamber membership benefits', r'Frequently Asked Questions', r'State Guides',
]


def _is_noisy(text: str) -> bool:
    t = (text or '').strip()
    if len(t) > 180:
        return True
    for p in _NOISE_PATTERNS:
        if re.search(p, t, re.I):
            return True
    return False


def generic_extract(html: str, base: str, state_stem: str = None) -> List[Dict]:
    soup = BeautifulSoup(html, 'html.parser')
    seen = {}
    results = []
    rules = get_rules(state_stem or '')
    mode = rules.get('mode', 'conservative')

    # Primary: list-unstyled lists (always used)
    for ul in soup.find_all('ul', class_='list-unstyled'):
        for li in ul.find_all('li'):
            raw = li.get_text(' ', strip=True)
            if not raw:
                continue
            name = re.sub(r'^[\u2022\-\*\+\s]+', '', raw).strip()
            name = re.split(r'\b(Website:|Phone:|Address:|Region:|Area:)', name)[0].strip()
            if not name:
                continue
            key = dedupe_key(name)
            if not key or key in seen:
                continue
            site = ''
            a = li.find('a', href=True)
            if a:
                site = normalize_site(a['href'].strip(), base)
            seen[key] = {'chamber_name': name, 'chamber_url': site}
            results.append(seen[key])

    # Secondary: anchors mentioning 'Chamber'
    for a in soup.find_all('a', href=True):
        text = (a.get_text(' ', strip=True) or '').strip()
        if not text:
            continue
        if mode == 'conservative':
            # only accept anchor if it contains 'chamber' and not noisy
            if 'chamber' not in text.lower():
                continue
            if _is_noisy(text):
                continue
        # in lenient mode accept more anchors
        key = dedupe_key(text)
        if not key or key in seen:
            continue
        seen[key] = {'chamber_name': text, 'chamber_url': normalize_site(a['href'].strip(), base)}
        results.append(seen[key])

    # Heading-based pass: capture li/anchors under headers
    for h in soup.find_all(re.compile(r'^h[1-6]$')):
        cur = h.next_sibling
        steps = 0
        while cur and steps < 60:
            if getattr(cur, 'name', None) and re.match(r'^h[1-6]$', cur.name):
                break
            if hasattr(cur, 'find_all'):
                for li in cur.find_all('li'):
                    raw = li.get_text(' ', strip=True).strip()
                    if not raw:
                        continue
                    name = re.split(r'\b(Website:|Phone:|Address:|Region:|Area:)', raw)[0].strip()
                    if mode == 'conservative' and _is_noisy(name):
                        continue
                    key = dedupe_key(name)
                    if not key or key in seen:
                        continue
                    a = li.find('a', href=True)
                    site = normalize_site(a['href'].strip(), base) if a else ''
                    seen[key] = {'chamber_name': name, 'chamber_url': site}
                    results.append(seen[key])
                for a in cur.find_all('a', href=True):
                    text = (a.get_text(' ', strip=True) or '').strip()
                    if not text:
                        continue
                    if mode == 'conservative' and _is_noisy(text):
                        continue
                    key = dedupe_key(text)
                    if not key or key in seen:
                        continue
                    seen[key] = {'chamber_name': text, 'chamber_url': normalize_site(a['href'].strip(), base)}
                    results.append(seen[key])
            cur = cur.next_sibling
            steps += 1

    return results


# Expose mapping for state names. For now use generic extractor for all states;
# per-state overrides can be added later.
def extract_state(state_filename: str, html: str, base: str) -> List[Dict]:
    # state_filename is like 'alabama.html' or 'colorado.html'
    return generic_extract(html, base)


if __name__ == '__main__':
    print('extractors module — intended to be imported')
