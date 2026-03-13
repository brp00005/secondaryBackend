import re
import time
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

# Constants
BASE_URL = "https://www.officialusa.com/stateguides/chambers"
ALL_STATES_URL = "https://www.officialusa.com/stateguides/chambers/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def fetch_with_retries(url: str, timeout: int = 15, retries: int = 3, backoff: float = 0.8) -> str:
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:
            last = e
            time.sleep(backoff * (1 + i))
    raise last


def normalize_site(s: str, base: str = BASE_URL) -> str:
    s = (s or '').strip()
    if not s:
        return ''
    if s.startswith('http://') or s.startswith('https://'):
        return s
    if s.startswith('//'):
        return 'https:' + s
    if re.match(r'^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', s):
        return 'https://' + s
    return urljoin(base, s)


def dedupe_key(name: str, website: str = '') -> str:
    """Generate a deduplication key from name and optionally website."""
    key_text = name + (website or '')
    return re.sub(r'[^a-z0-9]+', '', key_text.lower())


def write_workbook(outpath: str, sheets: Dict[str, pd.DataFrame]) -> None:
    """Write multiple DataFrames to an Excel workbook.
    
    Args:
        outpath: Path to the output Excel file
        sheets: Dict mapping sheet names to DataFrames
    """
    with pd.ExcelWriter(outpath, engine='openpyxl') as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def extract_expected_from_snapshot(soup) -> Optional[int]:
    """Extract the expected chamber count from the page HTML.
    
    Looks for patterns like "108+ local chambers" or similar counts mentioned on the page.
    
    Args:
        soup: BeautifulSoup object of the HTML page
        
    Returns:
        Integer count if found, None otherwise
    """
    # Look for patterns like "108+ local chambers" or "48 chambers"
    text = soup.get_text()
    
    # Pattern 1: "NNN+ local chambers"
    match = re.search(r'(\d+)\+?\s+(?:local\s+)?chambers', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Pattern 2: Look in the first few paragraphs for explicit counts
    for p in soup.find_all('p', limit=5):
        p_text = p.get_text()
        match = re.search(r'(\d+)\s+(?:local\s+)?chambers?', p_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None
