#!/usr/bin/env python3
"""
Get the actual chamber counts directly from the official websites.
Visits each state chamber page and extracts the expected count.
"""

import os
import sys
import time
import json
import re
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.helpers import HEADERS, BASE_URL, fetch_with_retries, extract_expected_from_snapshot

# List of all US states
STATES = [
    'Alabama', 'Arizona', 'Arkansas', 'California', 'Connecticut', 'Delaware',
    'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa',
    'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts',
    'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska',
    'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
    'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania',
    'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah',
    'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'
]

# Exclude these states
EXCLUDED_STATES = ['Alaska', 'Colorado', 'Vermont']

def get_state_url(state_name: str) -> str:
    """Convert state name to URL format."""
    return f"{BASE_URL}/{state_name.lower().replace(' ', '-')}.html"

def fetch_and_extract_count(state_name: str, use_snapshot: bool = True) -> Optional[int]:
    """Fetch the page and extract the expected chamber count."""
    
    # Try snapshot first if available
    if use_snapshot:
        snapshot_dir = os.path.join(os.path.dirname(__file__), '..', 'site_html')
        state_formatted = state_name.lower().replace(' ', '-')
        snapshot_path = os.path.join(snapshot_dir, f"{state_formatted}.html")
        
        if os.path.exists(snapshot_path):
            print(f"  Using snapshot: {snapshot_path}")
            try:
                with open(snapshot_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                    soup = BeautifulSoup(html, 'html.parser')
                    count = extract_expected_from_snapshot(soup)
                    return count
            except Exception as e:
                print(f"  Error reading snapshot: {e}")
                return None
    
    # Fetch from live URL
    state_url = get_state_url(state_name)
    print(f"  Fetching: {state_url}")
    
    try:
        html = fetch_with_retries(state_url, timeout=15, retries=3)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            count = extract_expected_from_snapshot(soup)
            return count
    except Exception as e:
        print(f"  Error fetching: {e}")
    
    return None

def main():
    """Main function to fetch all state counts."""
    
    results = {}
    
    print("Fetching chamber counts from all states...")
    print("=" * 70)
    
    for state in STATES:
        if state in EXCLUDED_STATES:
            print(f"\n{state:.<40} SKIPPED (Excluded)")
            continue
        
        print(f"\n{state:.<40} ", end='', flush=True)
        
        count = fetch_and_extract_count(state, use_snapshot=True)
        
        if count is not None:
            results[state] = count
            print(f"✓ {count} chambers")
        else:
            print(f"✗ Could not determine count")
            results[state] = None
        
        # Be polite with requests
        time.sleep(0.5)
    
    print("\n" + "=" * 70)
    print("\nSummary:")
    print("-" * 70)
    
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Save results to JSON
    results_file = os.path.join(output_dir, 'chamber_counts.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {results_file}")
    
    # Print summary
    found_count = sum(1 for c in results.values() if c is not None)
    not_found = sum(1 for c in results.values() if c is None)
    
    print(f"Total states processed: {len(results)}")
    print(f"Successfully determined: {found_count}")
    print(f"Failed to determine: {not_found}")
    
    # Print a list of states with counts
    print("\nCounts by state:")
    for state in sorted(results.keys()):
        count = results[state]
        if count is not None:
            print(f"  {state:.<30} {count:>5} chambers")
        else:
            print(f"  {state:.<30} {'N/A':>5}")

if __name__ == '__main__':
    main()
