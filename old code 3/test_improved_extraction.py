#!/usr/bin/env python3
"""
Improved extraction logic based on verified Colorado scraper.
Tests the new extraction against Alabama to see how many chambers we get.
"""
from bs4 import BeautifulSoup
import re
import sys
sys.path.append('.')
from scripts.helpers import dedupe_key, normalize_site

def extract_chambers_improved(html: str, state_name: str):
    """Extract chambers using improved logic from Colorado scraper."""
    soup = BeautifulSoup(html, 'html.parser')
    found = []
    
    # Strategy 1: Find list-unstyled ULs (common pattern)
    for ul in soup.find_all('ul', class_='list-unstyled'):
        for li in ul.find_all('li'):
            txt = (li.get_text(' ', strip=True) or '').strip()
            if txt:
                # Split off metadata (Website:, Phone:, etc.)
                name = re.split(r'\b(Website:|Phone:|Address:|Region:|Area:)', txt)[0].strip()
                if name and len(name) > 2:
                    found.append(name)
    
    # Strategy 2: Find headings and extract anchors that follow them
    for h in soup.find_all(re.compile(r'^h[1-6]$')):
        heading_txt = (h.get_text(' ', strip=True) or '').strip()
        if not heading_txt or len(heading_txt) < 2:
            continue
        
        # Look ahead up to 60 siblings for anchors
        cur = h.next_sibling
        steps = 0
        while cur and steps < 60:
            if getattr(cur, 'name', None) and re.match(r'^h[1-6]$', cur.name):
                break  # Stop at next heading
            
            if hasattr(cur, 'find_all'):
                # Extract from anchors
                for a in cur.find_all('a', href=True):
                    atext = (a.get_text(' ', strip=True) or '').strip()
                    if atext and len(atext) > 2:
                        found.append(atext)
                
                # Extract from list items
                for li in cur.find_all('li'):
                    ltxt = (li.get_text(' ', strip=True) or '').strip()
                    if ltxt:
                        name = re.split(r'\b(Website:|Phone:|Address:|Region:|Area:)', ltxt)[0].strip()
                        if name and len(name) > 2:
                            found.append(name)
            
            cur = cur.next_sibling
            steps += 1
    
    # Strategy 3: Find anchors with 'chamber' in text anywhere
    for a in soup.find_all('a', href=True):
        text = (a.get_text(' ', strip=True) or '').strip()
        if text and 'chamber' in text.lower() and len(text) > 2:
            found.append(text)
    
    # Deduplicate using same logic as template
    chambers = []
    seen_keys = set()
    
    for name in found:
        # Filter to entries containing 'chamber'
        if 'chamber' not in name.lower():
            continue
        
        key = dedupe_key(name, '')
        if key not in seen_keys:
            chambers.append({'chamber_name': name, 'website': ''})
            seen_keys.add(key)
    
    return chambers


# Test with Alabama
with open('site_html/alabama.html') as f:
    html = f.read()

chambers = extract_chambers_improved(html, 'Alabama')
print(f"Improved extraction for Alabama: {len(chambers)} chambers")
print("\nFirst 20:")
for i, c in enumerate(chambers[:20], 1):
    print(f"  {i}. {c['chamber_name']}")

# Compare to expected
print(f"\nExpected: 34")
print(f"Extracted: {len(chambers)}")
print(f"Match: {'✓' if len(chambers) == 34 else '✗'}")
