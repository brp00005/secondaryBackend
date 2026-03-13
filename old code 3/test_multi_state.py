#!/usr/bin/env python3
"""
Test the improved extraction across multiple states.
"""
import json
import os
import sys
sys.path.append('.')
from scripts.scrape_alabama_only import get_state_chambers

# Load our reference counts
with open('output/chamber_counts.json') as f:
    expected = json.load(f)

# Test a selection of states with verified counts
states_to_test = [
    ('Alabama', 'alabama'),
    ('Arizona', 'arizona'),
    ('California', 'california'),
    ('Florida', 'florida'),
    ('Illinois', 'illinois'),
    ('Ohio', 'ohio'),
    ('Texas', 'texas'),
    ('Wisconsin', 'wisconsin'),
]

print("State            | Expected | Extracted | Diff  | %Match")
print("-" * 60)

total_expected = 0
total_extracted = 0
matches = 0

for state, state_file in states_to_test:
    snapshot_path = f'site_html/{state_file}.html'
    
    if not os.path.exists(snapshot_path):
        print(f"{state:16} | {'N/A':8} | {'MISSING':9} | {'N/A':5} | N/A")
        continue
    
    exp_count = expected.get(state)
    if exp_count is None:
        print(f"{state:16} | {'NULL':8} | {'SKIP':9} | {'N/A':5} | N/A")
        continue
    
    chambers = get_state_chambers(state, snapshot_path)
    extracted_count = len(chambers)
    
    diff = extracted_count - exp_count
    pct = round(100 * extracted_count / exp_count) if exp_count > 0 else 0
    is_match = extracted_count == exp_count
    
    match_str = "✓" if is_match else "✗"
    
    print(f"{state:16} | {exp_count:8} | {extracted_count:9} | {diff:+5} | {pct:3}% {match_str}")
    
    total_expected += exp_count
    total_extracted += extracted_count
    if is_match:
        matches += 1

print("-" * 60)
total_pct = round(100 * total_extracted / total_expected) if total_expected > 0 else 0
print(f"{'TOTAL':16} | {total_expected:8} | {total_extracted:9} | {total_extracted - total_expected:+5} | {total_pct:3}%")
print(f"Perfect matches: {matches}/{len(states_to_test)}")
