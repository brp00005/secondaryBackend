#!/usr/bin/env python3
"""
Refined extraction: only get chambers from detailed sections, not the directory listing.
"""
from bs4 import BeautifulSoup
import re
import sys
sys.path.append('.')
from scripts.helpers import dedupe_key, normalize_site

def extract_chambers_refined(html: str, state_name: str):
    """Extract chambers from detailed sections only (cards with content)."""
    soup = BeautifulSoup(html, 'html.parser')
    found = []
    
    # Get all card divs (these are the detailed chambers)
    for card in soup.find_all('div', class_='card'):
        # Get the heading (h3, h4, h5, or h6)
        heading = card.find(['h3', 'h4', 'h5', 'h6'])
        if not heading:
            continue
        
        name = heading.get_text(strip=True)
        if not name or len(name) < 2:
            continue
        
        # Extract website from the card if available
        website = ''
        link = card.find('a', href=True)
        if link:
            website = link.get('href', '')
        
        # Filter to chambers (must have 'chamber' in name)
        if 'chamber' in name.lower():
            key = dedupe_key(name, website or '')
            found.append((key, name, website))
    
    # Deduplicate and preserve order
    chambers = []
    seen = set()
    for key, name, website in found:
        if key not in seen:
            chambers.append({'chamber_name': name, 'website': normalize_site(website) if website else ''})
            seen.add(key)
    
    return chambers


# Test with Alabama
print("Testing REFINED extraction (detailed cards only):")
with open('site_html/alabama.html') as f:
    html = f.read()

chambers = extract_chambers_refined(html, 'Alabama')
print(f"Refined extraction for Alabama: {len(chambers)} chambers\n")

print("Extracted chambers:")
for i, c in enumerate(chambers, 1):
    print(f"  {i}. {c['chamber_name']}")

# Compare to expected
print(f"\nExpected: 34")
print(f"Extracted: {len(chambers)}")
print(f"Match: {'✓' if len(chambers) == 34 else '✗'}")
