"""
Analyzer for US Chamber HTML structure to refine extraction logic
Run this to test and debug extraction on a single state
"""

import requests
from bs4 import BeautifulSoup
import json
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def analyze_html_structure(state_slug: str = 'alaska'):
    """Fetch and analyze the HTML structure of a chambers page."""
    
    url = f"https://www.uschamber.com/co/chambers/{state_slug}"
    print(f"Fetching {url}...")
    
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    html = response.text
    
    soup = BeautifulSoup(html, 'html.parser')
    
    print("\n" + "="*80)
    print(f"HTML STRUCTURE ANALYSIS FOR {state_slug.upper()}")
    print("="*80)
    
    # Find chambers container
    chambers_data = []
    
    # Look for common chamber container patterns
    print("\n1. Searching for chamber containers...")
    
    # Pattern 1: h3 tags (direct chamber names)
    h3_tags = soup.find_all('h3')
    print(f"\n   Found {len(h3_tags)} h3 tags")
    
    if h3_tags:
        print("\n   First 10 h3 tags:")
        for i, h3 in enumerate(h3_tags[:10]):
            print(f"     {i+1}. {h3.get_text(strip=True)[:80]}")
    
    # Pattern 2: Look for common chamber patterns
    print("\n2. Looking for chamber data patterns...")
    
    # Find all elements that might contain chamber info
    chambers_section = soup.find(string=re.compile(r'[\d\s]+Chambers', re.IGNORECASE))
    if chambers_section:
        parent = chambers_section.parent
        print(f"   Found chambers section: {chambers_section.strip()[:80]}")
        
        # Get the container
        container = parent.find_parent(['div', 'section', 'main'])
        if container:
            print(f"   Container tag: {container.name} with classes: {container.get('class', [])}")
    
    # Pattern 3: Extract chamber blocks more systematically
    print("\n3. Analyzing chamber block structure...")
    
    # Look for h3 followed by location info
    chamber_count = 0
    for h3 in h3_tags:
        text = h3.get_text(strip=True)
        
        # Skip navigation/header h3s
        if any(skip in text.lower() for skip in ['search', 'filter', 'additional', 'looking for', 'need to']):
            continue
        
        # Get next sibling elements
        next_elem = h3.next_sibling
        location = ""
        membership = ""
        elements_after = []
        
        count = 0
        while next_elem and count < 5:
            if hasattr(next_elem, 'name'):
                elem_text = next_elem.get_text(strip=True)
                if elem_text:
                    elements_after.append({
                        'tag': next_elem.name,
                        'text': elem_text[:100],
                        'class': next_elem.get('class', [])
                    })
                    
                    if 'U.S. Chamber Member' in elem_text:
                        membership = 'U.S. Chamber Member'
                    # Look for location (City, ST pattern)
                    if re.search(r'\w+,\s*[A-Z]{2}', elem_text):
                        location = elem_text
            next_elem = next_elem.next_sibling
            count += 1
        
        if elements_after:
            chamber_count += 1
            if chamber_count <= 5:  # Show first 5
                print(f"\n   Chamber {chamber_count}: {text}")
                print(f"   Location: {location}")
                print(f"   Membership: {membership}")
                print(f"   Followed by {len(elements_after)} elements:")
                for elem in elements_after:
                    print(f"      - <{elem['tag']}> {elem['text'][:80]}")
    
    # Pattern 4: Look for data attributes or JSON
    print("\n4. Checking for embedded data (script tags)...")
    scripts = soup.find_all('script', type='application/ld+json')
    if scripts:
        print(f"   Found {len(scripts)} LD+JSON scripts")
        for i, script in enumerate(scripts[:2]):
            try:
                data = json.loads(script.string)
                print(f"   Script {i+1} keys: {list(data.keys())[:10]}")
            except:
                pass
    
    # Pattern 5: Try to find main content div
    print("\n5. Looking for main content structure...")
    
    main = soup.find('main')
    if main:
        print(f"   Found <main> tag")
        # Count different elements
        h3_in_main = len(main.find_all('h3'))
        divs_in_main = len(main.find_all('div', class_='card'))
        print(f"   - h3 tags in main: {h3_in_main}")
        print(f"   - div.card tags: {divs_in_main}")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    analyze_html_structure('alaska')
