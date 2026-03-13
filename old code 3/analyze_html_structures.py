#!/usr/bin/env python3
"""
Analyze HTML structure of each state to identify extraction patterns.
This helps determine how chambers are organized on each state's page.
"""

import os
import json
import re
from bs4 import BeautifulSoup
from collections import defaultdict

def analyze_state_html(state_name_formatted):
    """Analyze a state's HTML and return structural information."""
    
    site_html_dir = os.path.join(os.path.dirname(__file__), '..', 'site_html')
    html_file = os.path.join(site_html_dir, f"{state_name_formatted}.html")
    
    if not os.path.exists(html_file):
        return None
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
    except:
        return None
    
    analysis = {
        'state': state_name_formatted,
        'post_content': False,
        'main_content_area': None,
        'link_count': 0,
        'h3_count': 0,
        'h2_count': 0,
        'h4_count': 0,
        'ul_lists': 0,
        'ol_lists': 0,
        'li_with_links': 0,
        'li_without_links': 0,
        'structure_type': 'unknown',
        'first_few_links': [],
        'headings': []
    }
    
    # Find main content area
    post_content = soup.find('div', class_='post-content')
    if post_content:
        analysis['post_content'] = True
        
        # Count structural elements
        analysis['link_count'] = len(post_content.find_all('a', href=True))
        analysis['h3_count'] = len(post_content.find_all('h3'))
        analysis['h2_count'] = len(post_content.find_all('h2'))
        analysis['h4_count'] = len(post_content.find_all('h4'))
        analysis['ul_lists'] = len(post_content.find_all('ul'))
        analysis['ol_lists'] = len(post_content.find_all('ol'))
        
        # Count li elements with/without links
        for li in post_content.find_all('li'):
            if li.find('a'):
                analysis['li_with_links'] += 1
            else:
                analysis['li_without_links'] += 1
        
        # Get sample links
        links = post_content.find_all('a', href=True)
        for link in links[:3]:
            text = link.get_text(strip=True)
            href = link.get('href')
            if text:
                analysis['first_few_links'].append({
                    'text': text[:50],
                    'href': href[:50]
                })
        
        # Get headings
        for h in post_content.find_all(['h2', 'h3', 'h4', 'h5'], limit=5):
            analysis['headings'].append({
                'tag': h.name,
                'text': h.get_text(strip=True)[:60]
            })
        
        # Determine structure type
        if analysis['h3_count'] > 20:
            analysis['structure_type'] = 'h3_list'
        elif analysis['li_with_links'] > 20:
            analysis['structure_type'] = 'li_with_links'
        elif analysis['li_without_links'] > 20:
            analysis['structure_type'] = 'li_text_only'
        elif analysis['link_count'] > 20:
            analysis['structure_type'] = 'mixed_links'
        
    return analysis

def main():
    """Main function."""
    
    site_html_dir = os.path.join(os.path.dirname(__file__), '..', 'site_html')
    html_files = [f[:-5] for f in os.listdir(site_html_dir) if f.endswith('.html') and f != 'all-states.html']
    
    # Exclude special states
    excluded = ['alaska', 'colorado', 'vermont']
    states = [s for s in html_files if s not in excluded]
    
    results = {}
    pattern_groups = defaultdict(list)
    
    for state in sorted(states):
        print(f"Analyzing {state}...", end='', flush=True)
        analysis = analyze_state_html(state)
        
        if analysis:
            results[state] = analysis
            pattern_groups[analysis['structure_type']].append(state)
            print(f" ✓ Type: {analysis['structure_type']}")
        else:
            print(f" ✗ Failed")
    
    # Print summary
    print("\n" + "="*80)
    print("STRUCTURE PATTERNS IDENTIFIED")
    print("="*80)
    
    for pattern_type in sorted(pattern_groups.keys()):
        states_with_pattern = pattern_groups[pattern_type]
        print(f"\n{pattern_type.upper()} ({len(states_with_pattern)} states):")
        for state in states_with_pattern[:10]:  # Show first 10
            analysis = results[state]
            print(f"  {state:20} - Links:{analysis['link_count']:3d} H3:{analysis['h3_count']:3d} LI:{analysis['li_with_links']:3d}")
        if len(states_with_pattern) > 10:
            print(f"  ... and {len(states_with_pattern) - 10} more")
    
    # Save analysis
    analysis_file = os.path.join(os.path.dirname(__file__), '..', 'output', 'html_structure_analysis.json')
    os.makedirs(os.path.dirname(analysis_file), exist_ok=True)
    
    with open(analysis_file, 'w') as f:
        json.dump({
            'analysis': results,
            'patterns': dict(pattern_groups)
        }, f, indent=2)
    
    print(f"\n\nAnalysis saved to: {analysis_file}")

if __name__ == '__main__':
    main()
