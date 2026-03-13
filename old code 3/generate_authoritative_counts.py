#!/usr/bin/env python3
"""
Run extraction on ALL states and generate authoritative chamber counts.
"""
import json
import os
import sys
sys.path.append('.')
from scripts.scrape_alabama_only import get_state_chambers

# Map state names to HTML file names
states_map = {
    'Alabama': 'alabama', 'Alaska': 'alaska', 'Arizona': 'arizona',
    'Arkansas': 'arkansas', 'California': 'california', 'Colorado': 'colorado',
    'Connecticut': 'connecticut', 'Delaware': 'delaware', 'Florida': 'florida',
    'Georgia': 'georgia', 'Hawaii': 'hawaii', 'Idaho': 'idaho', 'Illinois': 'illinois',
    'Indiana': 'indiana', 'Iowa': 'iowa', 'Kansas': 'kansas', 'Kentucky': 'kentucky',
    'Louisiana': 'louisiana', 'Maine': 'maine', 'Maryland': 'maryland',
    'Massachusetts': 'massachusetts', 'Michigan': 'michigan', 'Minnesota': 'minnesota',
    'Mississippi': 'mississippi', 'Missouri': 'missouri', 'Montana': 'montana',
    'Nebraska': 'nebraska', 'Nevada': 'nevada', 'New Hampshire': 'new-hampshire',
    'New Jersey': 'new-jersey', 'New Mexico': 'new-mexico', 'New York': 'new-york',
    'North Carolina': 'north-carolina', 'North Dakota': 'north-dakota', 'Ohio': 'ohio',
    'Oklahoma': 'oklahoma', 'Oregon': 'oregon', 'Pennsylvania': 'pennsylvania',
    'Rhode Island': 'rhode-island', 'South Carolina': 'south-carolina',
    'South Dakota': 'south-dakota', 'Tennessee': 'tennessee', 'Texas': 'texas',
    'Utah': 'utah', 'Vermont': 'vermont', 'Virginia': 'virginia',
    'Washington': 'washington', 'West Virginia': 'west-virginia',
    'Wisconsin': 'wisconsin', 'Wyoming': 'wyoming'
}

results = {}

print("Running extraction on all states...")
print("State                | Extracted | Status")
print("-" * 50)

for state, state_file in sorted(states_map.items()):
    snapshot_path = f'site_html/{state_file}.html'
    
    if not os.path.exists(snapshot_path):
        print(f"{state:20} | {'N/A':9} | MISSING")
        results[state] = None
        continue
    
    try:
        chambers = get_state_chambers(state, snapshot_path)
        count = len(chambers)
        results[state] = count
        print(f"{state:20} | {count:9} | OK")
    except Exception as e:
        print(f"{state:20} | {'ERROR':9} | {str(e)[:30]}")
        results[state] = None

# Save authoritative counts
with open('output/chamber_counts.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 50)
print(f"Authoritative chamber counts saved to output/chamber_counts.json")
print(f"Total states: {len(states_map)}")
print(f"States with data: {sum(1 for v in results.values() if v is not None)}")
print(f"States missing: {sum(1 for v in results.values() if v is None)}")
