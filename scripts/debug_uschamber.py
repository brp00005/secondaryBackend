"""
Debug script to analyze individual chamber extraction
"""

import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def debug_chambers(state_slug: str = 'alaska'):
    """Debug extraction for chambers."""
    
    url = f"https://www.uschamber.com/co/chambers/{state_slug}"
    print(f"Fetching {url}...")
    
    response = requests.get(url, headers=HEADERS, timeout=15)
    html = response.text
    
    soup = BeautifulSoup(html, 'html.parser')
    
    h3_tags = soup.find_all('h3')
    
    print(f"\nFound {len(h3_tags)} h3 tags")
    print("\nAnalyzing last 5 chambers (usually the problematic ones):\n")
    
    for h3 in h3_tags[-5:]:
        chamber_name = h3.get_text(strip=True)
        print(f"Chamber: {chamber_name}")
        
        # Get next 5 siblings
        current = h3.next_sibling
        sib_count = 0
        
        while current and sib_count < 5:
            if isinstance(current, str):
                text = current.strip()
                if text:
                    print(f"  [TEXT]: {text[:80]}")
            elif hasattr(current, 'name'):
                text = current.get_text(strip=True) if hasattr(current, 'get_text') else ''
                tag = current.name
                class_attr = current.get('class', [])
                print(f"  <{tag} class={class_attr}>: {text[:80]}")
                sib_count += 1
            
            current = current.next_sibling
        print()


if __name__ == '__main__':
    debug_chambers('alaska')
