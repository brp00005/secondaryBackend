
import os
import subprocess
import re
import json
import pandas as pd

def run_verifier():
    """
    Runs all state-specific scrapers and verifies their output counts.
    """
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(scripts_dir, '..'))
    output_dir = os.path.join(workspace_root, 'output')
    
    # Load reference counts from chamber_counts.json
    counts_file = os.path.join(output_dir, 'chamber_counts.json')
    if not os.path.exists(counts_file):
        print(f"ERROR: Reference counts file not found: {counts_file}")
        print("Please run 'python3 scripts/get_actual_chamber_counts.py' first.")
        return
    
    with open(counts_file, 'r') as f:
        reference_counts = json.load(f)
    
    # Find all state scraper scripts
    scraper_scripts = [f for f in os.listdir(scripts_dir) if f.startswith('scrape_') and f.endswith('_only.py')]
    
    # States to exclude from this verification run
    excluded_states = ['alaska', 'colorado', 'vermont']
    
    results = []
    
    for script in sorted(scraper_scripts):
        # Extract state name from filename, e.g., "scrape_new-york_only.py" -> "new-york"
        match = re.search(r'scrape_(.+?)_only\.py', script)
        if not match:
            continue
            
        state_name_formatted = match.group(1)
        
        if state_name_formatted in excluded_states:
            print(f"--- SKIPPING {state_name_formatted.upper()} (Excluded) ---")
            continue

        # Convert formatted name to the name used in arguments, e.g., "new-york" -> "New York"
        state_name_arg = state_name_formatted.replace('-', ' ').title()
        
        # Get expected count from reference file
        expected_count = reference_counts.get(state_name_arg)
        if expected_count is None:
            print(f"--- SKIPPING {state_name_arg} (No reference count found) ---")
            results.append({
                'State': state_name_arg,
                'Expected': 'N/A',
                'Extracted': 'N/A',
                'Status': 'SKIP',
                'Output File': 'N/A'
            })
            continue

        print(f"--- RUNNING: {state_name_arg} (Expected: {expected_count}) ---")
        
        script_path = os.path.join(scripts_dir, script)
        output_file = os.path.join(output_dir, f"{state_name_formatted}_chambers.xlsx")
        
        command = [
            'python3',
            script_path,
            state_name_arg,
            '--output', output_file
        ]
        
        try:
            # The script will use the snapshot by default if it exists
            process = subprocess.run(command, capture_output=True, text=True, check=True, timeout=60)
            
            stdout = process.stdout
            stderr = process.stderr

            # Parse output for the extracted count
            extracted_match = re.search(r'Found (\d+) chambers in', stdout)
            
            if stderr:
                print(f"STDERR for {state_name_arg}:\n{stderr}")

            if extracted_match:
                extracted = int(extracted_match.group(1))
                status = "PASS" if expected_count == extracted else "FAIL"
                
                result = {
                    'State': state_name_arg,
                    'Expected': expected_count,
                    'Extracted': extracted,
                    'Status': status,
                    'Output File': os.path.relpath(output_file, workspace_root)
                }
                results.append(result)
                print(f"Result: {status} (Expected: {expected_count}, Extracted: {extracted})")
            else:
                print(f"Could not parse extraction count from output for {state_name_arg}.")
                results.append({
                    'State': state_name_arg,
                    'Expected': expected_count,
                    'Extracted': 'N/A',
                    'Status': 'ERROR',
                    'Output File': 'N/A'
                })

        except subprocess.CalledProcessError as e:
            print(f"ERROR running script for {state_name_arg}:")
            print(e.stdout)
            print(e.stderr)
            results.append({
                'State': state_name_arg,
                'Expected': expected_count,
                'Extracted': 'N/A',
                'Status': 'CRASH',
                'Output File': 'N/A'
            })
        except subprocess.TimeoutExpired as e:
            print(f"TIMEOUT running script for {state_name_arg}")
            results.append({
                'State': state_name_arg,
                'Expected': expected_count,
                'Extracted': 'N/A',
                'Status': 'TIMEOUT',
                'Output File': 'N/A'
            })

        print("-" * (len(state_name_arg) + 14))
        print()

    # --- Summary ---
    print("\n\n==================== VERIFICATION SUMMARY ====================")
    if not results:
        print("No scripts were run.")
        return

    summary_df = pd.DataFrame(results)
    
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 120)
    
    print(summary_df.to_string(index=False))
    
    failures = summary_df[summary_df['Status'] != 'PASS']
    if not failures.empty:
        print(f"\n--- {len(failures)} STATES FAILED VERIFICATION ---")
        print("The following states need tuning:")
        for state in failures['State']:
            print(f"- {state}")
    else:
        print("\n--- ALL STATES PASSED VERIFICATION! ---")


if __name__ == '__main__':
    run_verifier()
