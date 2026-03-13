import os
import requests
from typing import List, Dict
from datetime import datetime


def _get_client_info():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None, None
    return url.rstrip("/"), key


def has_config() -> bool:
    url, key = _get_client_info()
    return bool(url and key)


def insert_discoveries(discoveries: List[Dict]) -> bool:
    """Insert a list of discovery dicts into the `discoveries` table.

    Each discovery should include at least: domain, url, source, discovered_at
    """
    supabase_url, supabase_key = _get_client_info()
    if not supabase_url or not supabase_key:
        print("Supabase not configured (set SUPABASE_URL and SUPABASE_KEY)")
        return False

    endpoint = f"{supabase_url}/rest/v1/discoveries"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    # ensure discovered_at set
    payload = []
    for d in discoveries:
        item = dict(d)
        if "discovered_at" not in item:
            item["discovered_at"] = datetime.utcnow().isoformat()
        payload.append(item)

    try:
        r = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        if r.status_code in (200, 201):
            print(f"  Inserted {len(payload)} rows into Supabase 'discoveries' table")
            return True
        else:
            print(f"  Supabase insert failed: {r.status_code} {r.text}")
            return False
    except Exception as e:
        print(f"  Supabase request error: {e}")
        return False
