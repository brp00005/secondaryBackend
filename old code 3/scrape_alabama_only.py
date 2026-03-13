
import argparse
import pandas as pd
from bs4 import BeautifulSoup
import sys
import os
import re

# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.helpers import (
    fetch_with_retries,
    normalize_site,
    dedupe_key,
    write_workbook,
    extract_expected_from_snapshot,
    BASE_URL,
    ALL_STATES_URL,
    HEADERS
)

def get_state_chambers(state_name, snapshot_path=None):
    """
    Extracts chamber of commerce information for a given state.

    Args:
        state_name (str): The name of the state to process.
        snapshot_path (str, optional): Path to a local HTML snapshot. Defaults to None.

    Returns:
        list: A list of dictionaries, each representing a chamber of commerce.
    """
    if snapshot_path:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            html = f.read()
        print(f"Successfully read snapshot for {state_name} from {snapshot_path}")
    else:
        state_url = f"{BASE_URL}/{state_name.lower()}.html"
        print(f"Fetching data for {state_name} from {state_url}...")
        html = fetch_with_retries(state_url, HEADERS)
        if not html:
            print(f"Failed to fetch data for {state_name}")
            return []

    soup = BeautifulSoup(html, 'html.parser')
    chambers = []
    seen_keys = set()

    # ==============================================================================
    # EXTRACTION LOGIC - Improved approach based on verified scrapers
    # ==============================================================================

    # PRIORITY 1: Extract from card elements (detailed chambers)
    # Skip accordion cards (FAQ sections)
    for card in soup.find_all('div', class_='card'):
        if card.find_parent('div', class_='accordion'):
            continue
        
        heading = card.find(['h3', 'h4', 'h5', 'h6'])
        if not heading:
            continue
        
        name = heading.get_text(strip=True)
        if not name or len(name) < 2:
            continue
        
        # Skip FAQ questions
        if re.match(r'^(What|How|Do|Can|Why|Where|Who|Is|Should|If)', name):
            continue
        
        if 'chamber' not in name.lower():
            continue
        
        website = ''
        link = card.find('a', href=True)
        if link:
            website = link.get('href', '')
        
        if website and not website.startswith('http'):
            website = 'https://' + website.lstrip('www.')
        
        key = dedupe_key(name, website or '')
        if key not in seen_keys:
            chambers.append({'chamber_name': name, 'website': normalize_site(website) if website else ''})
            seen_keys.add(key)

    # PRIORITY 2: Extract from list-unstyled ULs
    for ul in soup.find_all('ul', class_='list-unstyled'):
        for li in ul.find_all('li'):
            text = (li.get_text(' ', strip=True) or '').strip()
            if not text or len(text) < 2:
                continue
            
            # Split off metadata (Website:, Phone:, Address:, etc.)
            name = re.split(r'\b(Website:|Phone:|Address:|Region:|Area:)', text)[0].strip()
            if not name or len(name) < 2 or 'chamber' not in name.lower():
                continue
            
            website = ''
            link = li.find('a', href=True)
            if link:
                website = link.get('href', '')
            
            if website and not website.startswith('http'):
                website = 'https://' + website.lstrip('www.')
            
            key = dedupe_key(name, website or '')
            if key not in seen_keys:
                chambers.append({'chamber_name': name, 'website': normalize_site(website) if website else ''})
                seen_keys.add(key)

    # PRIORITY 3: Extract from headings followed by anchors/lists
    for h in soup.find_all(re.compile(r'^h[1-6]$')):
        heading_txt = (h.get_text(' ', strip=True) or '').strip()
        if not heading_txt or len(heading_txt) < 2:
            continue
        
        # Look ahead up to 60 siblings for anchors/list items
        cur = h.next_sibling
        steps = 0
        while cur and steps < 60:
            if getattr(cur, 'name', None) and re.match(r'^h[1-6]$', cur.name):
                break  # Stop at next heading
            
            if hasattr(cur, 'find_all'):
                # Extract from anchors
                for a in cur.find_all('a', href=True):
                    atext = (a.get_text(' ', strip=True) or '').strip()
                    if atext and len(atext) > 1 and 'chamber' in atext.lower():
                        website = a.get('href', '')
                        if website and not website.startswith('http'):
                            website = 'https://' + website.lstrip('www.')
                        
                        key = dedupe_key(atext, website or '')
                        if key not in seen_keys:
                            chambers.append({'chamber_name': atext, 'website': normalize_site(website) if website else ''})
                            seen_keys.add(key)
                
                # Extract from list items
                for li in cur.find_all('li'):
                    ltxt = (li.get_text(' ', strip=True) or '').strip()
                    if not ltxt or len(ltxt) < 2 or 'chamber' not in ltxt.lower():
                        continue
                    
                    name = re.split(r'\b(Website:|Phone:|Address:|Region:|Area:)', ltxt)[0].strip()
                    if not name or len(name) < 2:
                        continue
                    
                    website = ''
                    link = li.find('a', href=True)
                    if link:
                        website = link.get('href', '')
                    
                    if website and not website.startswith('http'):
                        website = 'https://' + website.lstrip('www.')
                    
                    key = dedupe_key(name, website or '')
                    if key not in seen_keys:
                        chambers.append({'chamber_name': name, 'website': normalize_site(website) if website else ''})
                        seen_keys.add(key)
            
            cur = cur.next_sibling
            steps += 1

    # ==============================================================================
    # END EXTRACTION LOGIC
    # ==============================================================================

    print(f"Found {len(chambers)} chambers in {state_name}.")
    return chambers

def extract_summary(soup):
    """
    Extracts summary data from the top of the state page.
    """
    summary_data = {}
    content_area = soup.find('div', class_='post-content')
    if not content_area:
        return summary_data

    # Logic adapted from Alaska scraper
    paragraphs = content_area.find_all('p', limit=5) # Check first few paragraphs
    for p in paragraphs:
        text = p.get_text()
        if ':' in text:
            lines = text.split('\\n')
            for line in lines:
                if ':' in line:
                    key, _, value = line.partition(':')
                    key = key.strip().lower().replace(' ', '_')
                    summary_data[key] = value.strip()
    return summary_data


def main(state_name, output_path, snapshot_path=None):
    """
    Main function to run the scraper for a single state.
    """
    if snapshot_path:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            html = f.read()
    else:
        state_url = f"{BASE_URL}/{state_name.lower()}.html"
        html = fetch_with_retries(state_url, HEADERS)

    if not html:
        print(f"Could not retrieve HTML for {state_name}. Exiting.")
        return

    soup = BeautifulSoup(html, 'html.parser')

    # Extract summary data
    summary = extract_summary(soup)
    summary_df = pd.DataFrame([summary])

    # Extract chamber listings
    chambers = get_state_chambers(state_name, snapshot_path)
    if not chambers:
        print(f"No chambers found for {state_name}. The script or page may need inspection.")
        # Still write an Excel file, but it will be empty except for summary
        chambers_df = pd.DataFrame([], columns=['chamber_name', 'website'])
    else:
        chambers_df = pd.DataFrame(chambers)

    # Verify counts
    expected_count = extract_expected_from_snapshot(soup)
    actual_count = len(chambers_df)
    print(f"Verification for {state_name}: Expected={expected_count}, Extracted={actual_count}")
    if expected_count is not None and actual_count != expected_count:
        print(f"WARNING: Mismatch for {state_name}! Expected {expected_count}, but found {actual_count}.")
    else:
        print(f"SUCCESS: Counts match for {state_name}.")


    # Write to Excel
    write_workbook(output_path, {
        'Summary': summary_df,
        'Chambers': chambers_df
    })
    print(f"Successfully wrote {len(chambers_df)} chambers to {output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape chamber of commerce data for a specific state.')
    parser.add_argument('state_name', type=str, help='The name of the state to scrape (e.g., "Alabama").')
    parser.add_argument('--output', '-o', default=None, help='Path to the output Excel file.')
    parser.add_argument('--snapshot', '-s', default=None, help='Path to a local HTML snapshot file.')
    args = parser.parse_args()

    state_name_formatted = args.state_name.replace(' ', '-').lower()

    if args.output:
        output_file = args.output
    else:
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output'))
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{state_name_formatted}_chambers.xlsx")

    if args.snapshot:
        snapshot_file = args.snapshot
    else:
        snapshot_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site_html'))
        snapshot_file = os.path.join(snapshot_dir, f"{state_name_formatted}.html")
        if not os.path.exists(snapshot_file):
            # Fallback to no snapshot if it doesn't exist
            print(f"Snapshot not found at {snapshot_file}. Will attempt to fetch live URL.")
            snapshot_file = None


    main(args.state_name, output_file, snapshot_file)
