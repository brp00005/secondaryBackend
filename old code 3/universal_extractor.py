#!/usr/bin/env python3
"""
Improved extraction logic that works for multiple state formats.
This module provides extraction functions for different HTML patterns.
"""

import re
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
from urllib.parse import urlparse

def extract_from_cards_and_links(soup) -> List[Dict]:
    """
    Extract chambers from card-based layouts with potential links.
    Works for states that use divs with class 'card' or 'col-md-X'.
    """
    chambers = []
    seen = set()
    
    # Pattern 1: Find h3/h4/h5 with class 'card-title' inside cards
   for heading in soup.find_all(['h3', 'h4', 'h5'], class_=re.compile(r'card-title|h\d')):
        name = heading.get_text(strip=True)
        if not name or len(name) < 3:
            continue
        
        # Look for website link nearby (in parent card or following elements)
        website = None
        parent = heading.find_parent(['div'], class_='card')
        if not parent:
            parent = heading.find_parent(['div'])
        
        if parent:
            # Look for links in the card/parent
            links = parent.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if href and ('http' in href or '.' in href):
                    website = href
                    break
            
            # If no link in card, look for website text pattern
            if not website:
                text = parent.get_text()
                website_match = re.search(r'Website:\s*([^\s<]+)', text, re.IGNORECASE)
                if website_match:
                    website = website_match.group(1)
        
        # Normalize website
        if not website:
            website = ''
        elif not website.startswith('http'):
            website = 'https://' + website.lstrip('www.')
        
        key = (name.lower(), website.lower())
        if key not in seen:
            chambers.append({'name': name, 'website': website})
            seen.add(key)
    
    return chambers


def extract_from_list_items(soup) -> List[Dict]:
    """
    Extract chambers from list items (ul/ol with li elements).
    """
    chambers = []
    seen = set()
    
    for li in soup.find_all('li'):
        text = li.get_text(strip=True)
        
        # Clean up bullet points and extra spaces
        text = text.lstrip('•').strip()
        
        if not text or len(text) < 3:
            continue
        
        # Check if this looks like a chamber name
        if 'chamber' not in text.lower() and 'commerce' not in text.lower():
            continue
        
        # Check for website link inside li
        website = None
        link = li.find('a', href=True)
        if link:
            website = link.get('href', '')
        
        if not website:
            website = ''
        elif not website.startswith('http'):
            website = 'https://' + website.lstrip('www.')
        
        key = (text.lower(), website.lower())
        if key not in seen:
            chambers.append({'name': text, 'website': website})
            seen.add(key)
    
    return chambers


def extract_chambers_universal(html: str) -> List[Dict]:
    """
    Universal extraction that works for most states.
    Combines multiple extraction strategies.
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try to find main content area
    main_content = None
    for selector in [
        {'class': 'post-content'},
        {'class': 'main-content'},
        {'class': 'content'},
        {'role': 'main'},
    ]:
        main_content = soup.find('div', selector)
        if main_content:
            break
    
    if not main_content:
        main_content = soup.find('body')
    
    chambers_from_cards = []
    chambers_from_lists = []
    
    if main_content:
        chambers_from_cards = extract_from_cards_and_links(main_content)
        chambers_from_lists = extract_from_list_items(main_content)
    else:
        chambers_from_cards = extract_from_cards_and_links(soup)
        chambers_from_lists = extract_from_list_items(soup)
    
    # Combine and deduplicate
    all_chambers = chambers_from_cards + chambers_from_lists
    seen = set()
    result = []
    
    for chamber in all_chambers:
        key = (chamber['name'].lower(), chamber['website'].lower())
        if key not in seen:
            result.append(chamber)
            seen.add(key)
    
    return result


if __name__ == '__main__':
    # Test with Alabama
    with open('/home/default/Desktop/duckduckgo-jobboard-crawler/site_html/alabama.html', 'r') as f:
        html = f.read()
    
    chambers = extract_chambers_universal(html)
    print(f"Extracted {len(chambers)} chambers from Alabama")
    print("\nFirst 10:")
    for i, c in enumerate(chambers[:10]):
        print(f"  {i+1}. {c['name']}")
