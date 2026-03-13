#!/usr/bin/env python3
import os

# Check if Alabama scraper has updated extraction logic
alabama_file = 'scripts/scrape_alabama_only.py'
with open(alabama_file) as f:
    alabama_content = f.read()

has_pass1 = 'Pass 1: Extract from headings' in alabama_content
has_pass2 = 'Pass 2: Extract from list items' in alabama_content

print(f"Alabama scraper has Pass 1: {has_pass1}")
print(f"Alabama scraper has Pass 2: {has_pass2}")

# Count total state scrapers with updated logic
import glob
state_files = glob.glob('scripts/scrape_*_only.py')
print(f"\nTotal state scrapers: {len(state_files)}")

# Count how many have updated logic
updated = 0
for f in state_files:
    with open(f) as fl:
        if 'Pass 1: Extract from headings' in fl.read():
            updated += 1

print(f"Scrapers with updated logic: {updated}")

# Now test if we can run the Alabama scraper
print("\n--- Running Alabama scraper ---")
from scripts.scrape_alabama_only import get_state_chambers
chambers = get_state_chambers('Alabama', 'site_html/alabama.html')
print(f"Chambers extracted: {len(chambers)}")
if chambers:
    print("First 3 chambers:")
    for c in chambers[:3]:
        print(f"  - {c['chamber_name']}: {c['website'][:40] if c['website'] else 'NO WEBSITE'}")
