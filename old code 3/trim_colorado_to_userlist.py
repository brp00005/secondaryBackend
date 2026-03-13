#!/usr/bin/env python3
"""Trim `output/colorado_chambers.xlsx` to the user-provided Colorado list (87 entries).

Creates `output/colorado_chambers_trimmed.xlsx` with rows matched to the user list
in the same order. Matching is case-insensitive and punctuation-agnostic.
"""
from pathlib import Path
import re
import pandas as pd

OUT = Path('output/colorado_chambers.xlsx')
OUT_TRIM = Path('output/colorado_chambers_trimmed.xlsx')

USER_LIST = [
    'Colorado Chamber of Commerce',
    'Denver Metro Chamber of Commerce',
    'South Metro Denver Chamber',
    'Colorado Springs Chamber & EDC',
    'Boulder Chamber of Commerce',
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
    'Pueblo Chamber of Commerce',
    'Canon City Chamber',
    'Trinidad/Las Animas County Chamber',
    'Alamosa County Chamber',
    'Monte Vista Chamber',
    'Pagosa Springs Chamber',
    'La Junta Chamber of Commerce',
    'Walsenburg Chamber',
    'Sterling Logan County Chamber',
    'Fort Morgan Area Chamber',
    'Yuma Chamber of Commerce',
    'Burlington Chamber of Commerce',
    'Limon Chamber of Commerce',
    'Lamar Chamber of Commerce',
    'Holyoke Chamber of Commerce',
    'Julesburg Chamber',
    'Grand Junction Area Chamber',
    'Fruita Chamber of Commerce',
    'Palisade Chamber of Commerce',
    'Montrose Chamber of Commerce',
    'Delta Area Chamber',
    'Cortez Area Chamber',
    'Dolores Chamber of Commerce',
    'Mancos Valley Chamber',
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
    'Colorado Black Chamber of Commerce',
    'Colorado Hispanic Chamber of Commerce',
    'Asian Chamber of Commerce Colorado',
    'Colorado LGBT Chamber of Commerce',
    "Colorado Women's Chamber",
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
        print('Missing input file:', OUT)
        return 2
    df = pd.read_excel(OUT).fillna('')
    name_col = 'chamber_name' if 'chamber_name' in df.columns else df.columns[0]
    candidates = [str(x) for x in df[name_col]]
    cand_map = {norm(c): i for i, c in enumerate(candidates)}

    rows = []
    missing = []
    used_keys = set()
    for u in USER_LIST:
        k = norm(u)
        found_idx = None
        if k in cand_map:
            found_idx = cand_map[k]
        else:
            # try containment
            for ck, idx in cand_map.items():
                if k and (k in ck or ck in k):
                    found_idx = idx
                    break
        if found_idx is not None:
            key = list(cand_map.keys())[list(cand_map.values()).index(found_idx)]
            if key in used_keys:
                # already used, skip duplicate
                continue
            used_keys.add(key)
            rows.append(df.iloc[found_idx])
        else:
            missing.append(u)

    out_df = pd.DataFrame(rows)
    out_df.to_excel(OUT_TRIM, index=False)
    print(f'Wrote trimmed workbook: {OUT_TRIM} ({len(out_df)} rows)')
    if missing:
        print('\nMissing from spreadsheet (not found):', len(missing))
        for m in missing:
            print('-', m)
    else:
        print('\nAll user-list items matched and written.')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
