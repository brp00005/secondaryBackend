#!/usr/bin/env python3
"""Debug Colorado extraction - find the missing 7 chambers."""
import sys
sys.path.append('.')
from scripts.scrape_alabama_only import get_state_chambers
from bs4 import BeautifulSoup

# Get Colorado chambers via scraper
chambers = get_state_chambers('Colorado', 'site_html/colorado.html')
print(f"Scraper extracted: {len(chambers)} chambers")
print(f"Data type: {type(chambers)}")
if chambers:
    print(f"First item type: {type(chambers[0])}")
    print(f"First item: {chambers[0]}")

# Now look at the raw HTML to find what might be missed
with open('site_html/colorado.html') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("\n" + "="*75)
print("ANALYZING ALTERNATIVE EXTRACTION METHODS")
print("="*75)

# Count different element types
cards = soup.find_all('div', class_='card')
print(f"Div.card elements: {len(cards)}")

# Check for list items
lists = soup.find_all('li')
print(f"List items <li>: {len(lists)}")

# Accordion cards
accordion_cards = soup.find_all('div', class_='card-header')
print(f"Accordion card headers: {len(accordion_cards)}")

# Check for list-unstyled
unstyled_lists = soup.find_all('ul', class_='list-unstyled')
print(f"Unstyled lists: {len(unstyled_lists)}")

text_content = []
for ul in unstyled_lists:
    items = ul.find_all('li')
    text_content.append(f"UL with {len(items)} items")

print(f"\nUnstyled list details:")
for detail in text_content:
    print(f"  - {detail}")

# Look for text nodes that might be chamber names
print("\n" + "="*75)
print("CHECKING TEXT PATTERNS:")
print("="*75)

# Look at all direct text in main content
all_text = soup.get_text(separator='\n', strip=True)
lines = [line.strip() for line in all_text.split('\n') if line.strip()]
print(f"Total text lines: {len(lines)}")

# Print lines that look like chamber names (proper case, 20-80 chars)
potential_names = []
for line in lines:
    if 20 < len(line) < 80 and not any(keyword in line.lower() for keyword in 
        ['faq', 'question', 'what', 'how', 'phone', 'email', 'address', 'website']):
        if line[0].isupper():
            potential_names.append(line)

print(f"\nPotential chamber names (first 100):")
for i, name in enumerate(potential_names[:100], 1):
    print(f"{i:3}. {name}")
