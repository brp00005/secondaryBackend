#!/usr/bin/env python3
"""
Comprehensive verification: Extract all states and compare against authoritative counts.
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

# Load authoritative counts
with open('output/chamber_counts.json') as f:
    expected = json.load(f)

print("Comprehensive Verification Report")
print("=" * 75)
print(f"{'State':<20} | {'Target':>8} | {'Extracted':>9} | {'Diff':>5} | {'Status':<10}")
print("-" * 75)

perfect = 0
close = 0  # Within 10%
off = 0
failed = 0

for state in sorted(states_map.keys()):
    state_file = states_map[state]
    snapshot_path = f'site_html/{state_file}.html'
    
    if not os.path.exists(snapshot_path):
        print(f"{state:<20} | {'N/A':>8} | {'MISSING':>9} | {'N/A':>5} | {'SKIP':<10}")
        failed += 1
        continue
    
    exp_count = expected.get(state, 0)
    
    try:
        chambers = get_state_chambers(state, snapshot_path)
        extracted = len(chambers)
        
        diff = extracted - exp_count
        pct_diff = abs(diff) / exp_count * 100 if exp_count > 0 else 100
        
        if diff == 0:
            status = "✓ PASS"
            perfect += 1
        elif pct_diff <= 10:
            status = "~ CLOSE"
            close += 1
        else:
            status = "✗ OFF"
            off += 1
        
        print(f"{state:<20} | {exp_count:>8} | {extracted:>9} | {diff:>+5} | {status:<10}")
        
    except Exception as e:
        print(f"{state:<20} | {exp_count:>8} | {'ERROR':>9} | {'N/A':>5} | {str(e)[:10]:<10}")
        failed += 1

print("-" * 75)
print(f"\nSummary:")
print(f"  Perfect matches (0% diff):  {perfect:2}/{len(states_map)}")
print(f"  Close matches (≤10% diff):  {close:2}/{len(states_map)}")
print(f"  Off matches (>10% diff):    {off:2}/{len(states_map)}")
print(f"  Failed/Missing:             {failed:2}/{len(states_map)}")
