#!/usr/bin/env python3
"""Run proxy-related unit checks without pytest available."""
import time
import json
import sys
import tempfile
from pathlib import Path

# ensure repo root is on sys.path so imports like `from crawler import ...` work
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crawler import DuckDuckGoJobBoardCrawler


def run():
    proxies = ["http://p1:1111", "http://p2:2222"]
    with tempfile.TemporaryDirectory() as td:
        stats_file = Path(td) / "stats.json"
        c = DuckDuckGoJobBoardCrawler(proxies=proxies, proxy_ban_seconds=1, proxy_stats_file=str(stats_file))

        p1 = c._get_next_proxy()
        assert p1 and p1.get("http") == proxies[0], "first rotation mismatch"
        p2 = c._get_next_proxy()
        assert p2 and p2.get("http") == proxies[1], "second rotation mismatch"

        c._ban_proxy(p1)
        nextp = c._get_next_proxy()
        assert nextp and nextp.get("http") == proxies[1], "expected p2 after banning p1"

        c.save_proxy_stats(str(stats_file))
        data = json.loads(stats_file.read_text())
        assert proxies[0] in data, "stats should include p1"
        assert data[proxies[0]].get("banned_until") is not None

        time.sleep(1.1)
        found = False
        for _ in range(10):
            np = c._get_next_proxy()
            if np and np.get("http") == proxies[0]:
                found = True
                break
        assert found, "p1 should be available after ban expires"

    print("Proxy checks passed")


if __name__ == "__main__":
    try:
        run()
    except AssertionError as e:
        print("Test failed:", e)
        sys.exit(2)
    except Exception as e:
        print("Unexpected error:", e)
        sys.exit(3)