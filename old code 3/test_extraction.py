#!/usr/bin/env python3
from bs4 import BeautifulSoup

# Load Alabama HTML
with open('site_html/alabama.html') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# Find all h3/h4/h5
heads = soup.find_all(['h3', 'h4', 'h5'])
print(f'Total headings: {len(heads)}')

# Count how many have 'chamber' in text
chamber_heads = [h for h in heads if 'chamber' in h.get_text().lower()]
print(f'Headings with chamber: {len(chamber_heads)}')

# Print first 10 with chamber
print('\nFirst 10 headings with chamber:')
for h in chamber_heads[:10]:
    text = h.get_text(strip=True)[:80]
    parent_card = h.find_parent('div', class_='card')
    print(f'  - {text} | has .card: {parent_card is not None}')

# Count list items 
lis = soup.find_all('li')
chamber_lis = [l for l in lis if 'chamber' in l.get_text().lower()]
print(f'\nTotal list items: {len(lis)}')
print(f'List items with chamber: {len(chamber_lis)}')
print('\nFirst 10 list items with chamber:')
for li in chamber_lis[:10]:
    text = li.get_text(strip=True).lstrip('•').strip()[:80]
    link = li.find('a', href=True)
    print(f'  - {text} | has link: {link is not None}')
