"""
Scraper for US Chamber of Commerce directories
Scrapes chamber listings from https://www.uschamber.com/co/chambers/{state}
"""

import argparse
import pandas as pd
from bs4 import BeautifulSoup
import sys
import os
import re
import json
from typing import List, Dict, Optional
from datetime import datetime

# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.helpers import (
    fetch_with_retries,
    normalize_site,
    dedupe_key,
    write_workbook,
    HEADERS
)

# Base URL for US Chamber of Commerce
USCHAMBER_BASE_URL = "https://www.uschamber.com/co/chambers"

# State slug mappings (state_name -> URL slug)
STATE_SLUGS = {
    'alabama': 'alabama',
    'alaska': 'alaska',
    'arizona': 'arizona',
    'arkansas': 'arkansas',
    'california': 'california',
    'colorado': 'colorado',
    'connecticut': 'connecticut',
    'delaware': 'delaware',
    'florida': 'florida',
    'georgia': 'georgia',
    'hawaii': 'hawaii',
    'idaho': 'idaho',
    'illinois': 'illinois',
    'indiana': 'indiana',
    'iowa': 'iowa',
    'kansas': 'kansas',
    'kentucky': 'kentucky',
    'louisiana': 'louisiana',
    'maine': 'maine',
    'maryland': 'maryland',
    'massachusetts': 'massachusetts',
    'michigan': 'michigan',
    'minnesota': 'minnesota',
    'mississippi': 'mississippi',
    'missouri': 'missouri',
    'montana': 'montana',
    'nebraska': 'nebraska',
    'nevada': 'nevada',
    'new hampshire': 'new-hampshire',
    'new jersey': 'new-jersey',
    'new mexico': 'new-mexico',
    'new york': 'new-york',
    'north carolina': 'north-carolina',
    'north dakota': 'north-dakota',
    'ohio': 'ohio',
    'oklahoma': 'oklahoma',
    'oregon': 'oregon',
    'pennsylvania': 'pennsylvania',
    'rhode island': 'rhode-island',
    'south carolina': 'south-carolina',
    'south dakota': 'south-dakota',
    'tennessee': 'tennessee',
    'texas': 'texas',
    'utah': 'utah',
    'vermont': 'vermont',
    'virginia': 'virginia',
    'washington': 'washington',
    'west virginia': 'west-virginia',
    'wisconsin': 'wisconsin',
    'wyoming': 'wyoming',
}

# States to process (50 states)
ALL_STATES = list(STATE_SLUGS.keys())


def extract_chambers_from_html(html: str, state_name: str) -> List[Dict]:
    """
    Extracts chamber of commerce information from HTML.
    
    The page structure contains:
    - h3 tags with chamber names
    - Followed by p tag(s) with location and/or membership info
    
    Args:
        html (str): The HTML content to parse
        state_name (str): The state name for reference
        
    Returns:
        List[Dict]: List of chamber dictionaries with keys:
                   - chamber_name: Name of the chamber
                   - city: City location  
                   - state: State abbreviation
                   - membership_status: "U.S. Chamber Member" or empty
    """
    soup = BeautifulSoup(html, 'html.parser')
    chambers = []
    seen_keys = set()
    
    # State abbreviation mapping for all US states
    state_abbr_map = {
        'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
        'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
        'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
        'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
        'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
        'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
        'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
        'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
        'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
        'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
        'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
        'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
        'wisconsin': 'WI', 'wyoming': 'WY',
    }
    
    state_name_lower = state_name.lower()
    expected_state_abbr = state_abbr_map.get(state_name_lower, state_name.upper()[:2])
    
    # Find all h3 tags which contain chamber names
    h3_tags = soup.find_all('h3')
    
    for h3 in h3_tags:
        chamber_name = h3.get_text(strip=True)
        
        # Skip empty or too short names
        if not chamber_name or len(chamber_name) < 2:
            continue
        
        # Skip navigation/header elements
        skip_keywords = ['search', 'filter', 'by city', 'latest on', 'additional links', 'all states', 'welcome to']
        if any(keyword in chamber_name.lower() for keyword in skip_keywords):
            continue
        
        # Get the deduplication key to avoid duplicates
        key = dedupe_key(chamber_name)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        
        # Extract location and membership status from following p tags
        membership_status = ""
        city = ""
        
        # The structure alternates between:
        # - h3: Chamber Name
        # - p: Either membership status OR city info
        # - p: (optional) the other piece of info
        
        current = h3.next_sibling
        p_texts = []
        
        # Collect up to 3 p tags following the h3
        while current and len(p_texts) < 3:
            if isinstance(current, str):
                if current.strip():
                    pass  # Skip standalone text
            elif hasattr(current, 'name') and current.name == 'p':
                text = current.get_text(strip=True)
                if text:
                    p_texts.append(text)
            elif hasattr(current, 'name') and current.name == 'h3':
                # Hit the next chamber, stop
                break
            
            current = current.next_sibling
        
        # Parse collected text
        for text in p_texts:
            if 'U.S. Chamber Member' in text:
                membership_status = 'U.S. Chamber Member'
            elif ',' in text and len(text) < 50:  # Location format: "City, ST"
                city = text
        
        # Extract state abbreviation from city if present
        state_abbr = expected_state_abbr
        if city:
            # Extract state code from "City, ST" format
            match = re.search(r',\s*([A-Z]{2})\s*$', city)
            if match:
                state_abbr = match.group(1)
        
        # Only add if we have a chamber name (city is optional in case of data issues)
        if chamber_name:
            chambers.append({
                'chamber_name': chamber_name,
                'city': city,
                'state': state_abbr,
                'membership_status': membership_status
            })
    
    return chambers


def get_state_chambers(state_name: str, snapshot_path: Optional[str] = None) -> List[Dict]:
    """
    Extracts chamber of commerce information for a given state from uschamber.com
    
    Args:
        state_name (str): The name of the state to process
        snapshot_path (str, optional): Path to a local HTML snapshot
        
    Returns:
        list: A list of dictionaries, each representing a chamber of commerce
    """
    state_lower = state_name.lower()
    
    if snapshot_path:
        # Load from local snapshot
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            html = f.read()
        print(f"✓ Loaded snapshot for {state_name} from {snapshot_path}")
    else:
        # Fetch from web
        state_slug = STATE_SLUGS.get(state_lower, state_lower)
        state_url = f"{USCHAMBER_BASE_URL}/{state_slug}"
        print(f"→ Fetching {state_name} from {state_url}...")
        
        try:
            html = fetch_with_retries(state_url, timeout=15, retries=3)
            if not html:
                print(f"✗ Failed to fetch data for {state_name}")
                return []
            print(f"✓ Retrieved {len(html)} bytes for {state_name}")
        except Exception as e:
            print(f"✗ Error fetching {state_name}: {e}")
            return []
    
    # Extract chambers from HTML
    chambers = extract_chambers_from_html(html, state_name)
    print(f"✓ Extracted {len(chambers)} chambers from {state_name}")
    
    return chambers


def scrape_all_states(output_file: str = "uschamber_all_states.csv") -> None:
    """
    Scrapes all states and saves results to CSV.
    
    Args:
        output_file (str): Output file path for the CSV
    """
    all_chambers = []
    failed_states = []
    successfull_states = []
    
    print(f"\n{'='*70}")
    print(f"  US CHAMBER OF COMMERCE SCRAPER - ALL STATES")
    print(f"  Target: {len(ALL_STATES)} states")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    for i, state in enumerate(ALL_STATES, 1):
        print(f"\n[{i}/{len(ALL_STATES)}] Processing {state.title()}...")
        try:
            chambers = get_state_chambers(state)
            if chambers:
                all_chambers.extend(chambers)
                successfull_states.append(state)
                print(f"    → Total so far: {len(all_chambers)} chambers")
            else:
                failed_states.append(state)
        except Exception as e:
            print(f"    ✗ Exception: {e}")
            failed_states.append(state)
    
    # Save results
    if all_chambers:
        df = pd.DataFrame(all_chambers)
        df = df.sort_values(['state', 'chamber_name']).reset_index(drop=True)
        
        output_path = os.path.join('output', output_file)
        os.makedirs('output', exist_ok=True)
        df.to_csv(output_path, index=False)
        
        print(f"\n{'='*70}")
        print(f"  SCRAPING COMPLETE")
        print(f"  Total chambers found: {len(all_chambers)}")
        print(f"  Successful states: {len(successfull_states)}")
        print(f"  Failed states: {len(failed_states)}")
        print(f"  Output file: {output_path}")
        print(f"  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        if failed_states:
            print(f"Failed states: {', '.join(failed_states)}\n")
        
        # Print sample
        print("Sample of extracted data:")
        print(df.head(10).to_string())
    else:
        print("✗ No chambers extracted!")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape US Chamber of Commerce directories'
    )
    parser.add_argument(
        '--state',
        type=str,
        help='Scrape specific state (e.g., alaska, california)'
    )
    parser.add_argument(
        '--snapshot',
        type=str,
        help='Path to local HTML snapshot file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='uschamber_all_states.csv',
        help='Output CSV file name (in output/ directory)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Scrape all states (default)'
    )
    
    args = parser.parse_args()
    
    if args.state:
        state_lower = args.state.lower()
        if state_lower not in STATE_SLUGS:
            print(f"Error: Unknown state '{args.state}'")
            print(f"Available states: {', '.join(sorted(STATE_SLUGS.keys()))}")
            sys.exit(1)
        
        chambers = get_state_chambers(state_lower, args.snapshot)
        
        if chambers:
            df = pd.DataFrame(chambers)
            print("\nExtracted chambers:")
            print(df.to_string())
            
            # Save to output
            output_path = os.path.join('output', f'uschamber_{state_lower}.csv')
            os.makedirs('output', exist_ok=True)
            df.to_csv(output_path, index=False)
            print(f"\nSaved to {output_path}")
    else:
        # Default: scrape all states
        scrape_all_states(args.output)


if __name__ == '__main__':
    main()
