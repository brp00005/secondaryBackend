#!/usr/bin/env python3
"""
Further refined extraction: only get chambers from card elements, skip FAQs and other content.
"""
from bs4 import BeautifulSoup
import re
import sys
sys.path.append('.')
from scripts.helpers import dedupe_key, normalize_site

def extract_chambers_final(html: str, state_name: str):
    """Extract chambers from card elements only, skip FAQ headings."""
    soup = BeautifulSoup(html, 'html.parser')
    found = []
    
    # Get all card divs (these are the detailed chambers)
    # Skip cards that are inside an accordion (FAQ section)
    for card in soup.find_all('div', class_='card'):
        # Skip if this card is inside an accordion (FAQ)
        if card.find_parent('div', class_='accordion'):
            continue
        
        # Get the card heading (h3, h4, h5, or h6)
        heading = card.find(['h3', 'h4', 'h5', 'h6'])
        if not heading:
            continue
        
        name = heading.get_text(strip=True)
        if not name or len(name) < 2:
            continue
        
        # Skip FAQ questions (they often start with "What", "How", "Do", "Can", "Why")
        if re.match(r'^(What|How|Do|Can|Why|Where|Who|Is|Should|If)', name):
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
print("Testing FINAL extraction (cards only, no FAQ):")
with open('site_html/alabama.html') as f:
    html = f.read()

chambers = extract_chambers_final(html, 'Alabama')
print(f"Final extraction for Alabama: {len(chambers)} chambers\n")

print("Extracted chambers:")
for i, c in enumerate(chambers, 1):
    print(f"  {i}. {c['chamber_name']}")

# Compare to expected
print(f"\nExpected: 34")
print(f"Extracted: {len(chambers)}")
print(f"Match: {'✓' if len(chambers) == 34 else '✗'}")
