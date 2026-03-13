import time
import json
from pathlib import Path

from crawler import DuckDuckGoJobBoardCrawler


def test_proxy_rotation_and_ban(tmp_path):
    proxies = ["http://p1:1111", "http://p2:2222"]
    stats_file = str(tmp_path / "stats.json")

    c = DuckDuckGoJobBoardCrawler(proxies=proxies, proxy_ban_seconds=1, proxy_stats_file=stats_file)

    # rotation order
    p1 = c._get_next_proxy()
    assert p1 and p1.get("http") == proxies[0]
    p2 = c._get_next_proxy()
    assert p2 and p2.get("http") == proxies[1]

    # ban first proxy
    c._ban_proxy(p1)

    # next available should be p2
    nextp = c._get_next_proxy()
    assert nextp and nextp.get("http") == proxies[1]

    # stats persisted
    c.save_proxy_stats(stats_file)
    data = json.loads(Path(stats_file).read_text())
    assert proxies[0] in data
    # banned_until should be present in stats for the banned proxy
    assert data[proxies[0]].get("banned_until") is not None

    # after ban expires, p1 should become available again
    time.sleep(1.1)
    found = False
    # rotate a few times to allow index movement
    for _ in range(10):
        np = c._get_next_proxy()
        if np and np.get("http") == proxies[0]:
            found = True
            break
    assert found, "proxy p1 should be available after ban expires"
