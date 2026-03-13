#!/usr/bin/env python3
"""Verify produced `output/colorado_chambers.xlsx` contains the 87 user-provided Colorado entities.

This script only verifies presence (case-insensitive, punctuation-agnostic) and
does not hardcode anything into the scraper itself.
"""
from pathlib import Path
import re
import pandas as pd

OUT = Path('output/colorado_chambers.xlsx')

USER_LIST = [
    # Statewide & Major Metro (5)
    'Colorado Chamber of Commerce',
    'Denver Metro Chamber of Commerce',
    'South Metro Denver Chamber',
    'Colorado Springs Chamber & EDC',
    'Boulder Chamber of Commerce',
    # Front Range Regional (23) - Denver Metro Area (12)
    'Aurora Chamber of Commerce',
    'Arvada Chamber of Commerce',
    'Westminster Chamber of Commerce',
    'Lakewood Chamber of Commerce',
    'Thornton Chamber of Commerce',
    'Northglenn-Thornton Rotary',
    'Englewood Chamber of Commerce',
    'Littleton Business Chamber',
    'Cherry Creek Chamber',
    'Golden Chamber of Commerce',
    'Castle Rock Chamber',
    'Parker Chamber of Commerce',
    # Northern Front Range (11)
    'Fort Collins Area Chamber',
    'Loveland Chamber of Commerce',
    'Greeley Area Chamber',
    'Longmont Area Chamber',
    'Broomfield Chamber of Commerce',
    'Lafayette Chamber of Commerce',
    'Louisville Chamber of Commerce',
    'Erie Chamber of Commerce',
    'Brighton Chamber of Commerce',
    'Windsor Chamber of Commerce',
    'Evans Area Chamber',
    # Mountain Communities (19) - Ski Resort Areas (10)
    'Vail Valley Partnership',
    'Aspen Chamber Resort Association',
    'Breckenridge Tourism Office',
    'Steamboat Springs Chamber',
    'Telluride Tourism Board',
    'Winter Park & Fraser Chamber',
    'Crested Butte/Mt Crested Butte Chamber',
    'Durango Area Tourism Office',
    'Keystone Resort Chamber',
    'Copper Mountain Chamber',
    # Mountain Towns (9)
    'Estes Park Chamber',
    'Grand Lake Area Chamber',
    'Idaho Springs Chamber',
    'Georgetown Community Center',
    'Glenwood Springs Chamber',
    'Leadville/Lake County Chamber',
    'Buena Vista Chamber',
    'Salida Chamber of Commerce',
    'Ouray Chamber Resort Association',
    'Silverton Chamber of Commerce',
    # Southern & Eastern Colorado (16) - Southern (8)
    'Pueblo Chamber of Commerce',
    'Canon City Chamber',
    'Trinidad/Las Animas County Chamber',
    'Alamosa County Chamber',
    'Monte Vista Chamber',
    'Pagosa Springs Chamber',
    'La Junta Chamber of Commerce',
    'Walsenburg Chamber',
    # Eastern Plains (8)
    'Sterling Logan County Chamber',
    'Fort Morgan Area Chamber',
    'Yuma Chamber of Commerce',
    'Burlington Chamber of Commerce',
    'Limon Chamber of Commerce',
    'Lamar Chamber of Commerce',
    'Holyoke Chamber of Commerce',
    'Julesburg Chamber',
    # Western Slope (13) - Grand Junction & Mesa County (3)
    'Grand Junction Area Chamber',
    'Fruita Chamber of Commerce',
    'Palisade Chamber of Commerce',
    # Southwest (5)
    'Montrose Chamber of Commerce',
    'Delta Area Chamber',
    'Cortez Area Chamber',
    'Dolores Chamber of Commerce',
    'Mancos Valley Chamber',
    # Northwest (5)
    'Craig Chamber of Commerce',
    'Meeker Chamber of Commerce',
    'Rangely Area Chamber',
    'Rifle Area Chamber',
    'Carbondale Chamber',
    'Basalt Chamber of Commerce',
    'Eagle Valley Chamber',
    'Kremmling Area Chamber',
    'Granby Chamber of Commerce',
    'Hot Sulphur Springs Chamber',
    # Specialty & Industry (11) - Diversity Chambers (5)
    'Colorado Black Chamber of Commerce',
    'Colorado Hispanic Chamber of Commerce',
    'Asian Chamber of Commerce Colorado',
    'Colorado LGBT Chamber of Commerce',
    'Colorado Women\'s Chamber',
    # Industry Associations (6)
    'Colorado Restaurant Association',
    'Colorado Hotel & Lodging Association',
    'Colorado Contractors Association',
    'Colorado Technology Association',
    'Colorado Manufacturing Association',
    'Colorado Oil & Gas Association',
]


def norm(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', (s or '').lower())


def main():
    if not OUT.exists():
        print('Missing output file:', OUT)
        return 2
    df = pd.read_excel(OUT).fillna('')
    candidates = [str(x) for x in df.get('chamber_name', df.columns[0])]
    cand_norm = {norm(c): c for c in candidates}

    missing = []
    matched = []
    for u in USER_LIST:
        k = norm(u)
        if k in cand_norm:
            matched.append(u)
        else:
            # try fuzzy containment
            found = False
            for ck in cand_norm:
                if k and (k in ck or ck in k):
                    matched.append(u)
                    found = True
                    break
            if not found:
                missing.append(u)

    print(f'Matched {len(matched)} of {len(USER_LIST)} user-listed entities')
    if missing:
        print('\nMissing items:')
        for m in missing:
            print('-', m)
    else:
        print('\nAll user-listed entities found in spreadsheet')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
