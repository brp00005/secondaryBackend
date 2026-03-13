import os
from importlib.machinery import SourceFileLoader

# Shim to load legacy helpers from likely legacy locations
candidates = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'old code v2', 'helpers.py')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'old code 3', 'helpers.py')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'old code', 'helpers.py')),
]
legacy = None
legacy_path = None
for p in candidates:
    if os.path.exists(p):
        legacy_path = p
        legacy = SourceFileLoader('legacy_helpers', legacy_path).load_module()
        break
if legacy is None:
    raise ImportError(f"Legacy helpers not found; looked in: {candidates}")

# expose commonly used symbols
fetch_with_retries = legacy.fetch_with_retries
normalize_site = legacy.normalize_site
dedupe_key = legacy.dedupe_key
write_workbook = getattr(legacy, 'write_workbook', None)
HEADERS = getattr(legacy, 'HEADERS', {})
