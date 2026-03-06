"""Headless crawler using Playwright to fetch DuckDuckGo search results.

This tries to render the page like a real browser to avoid bot challenges.
"""
import json
from pathlib import Path
from typing import List, Dict

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def run_search(query: str, limit: int = 50) -> List[Dict]:
    if sync_playwright is None:
        raise RuntimeError("Playwright not installed")

    results: List[Dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://duckduckgo.com/?q={query}")
        # wait for results
        page.wait_for_selector("a.result__a", timeout=10000)
        anchors = page.query_selector_all("a.result__a")
        for a in anchors[:limit]:
            title = a.inner_text()
            href = a.get_attribute("href")
            results.append({"title": title, "url": href})
        browser.close()
    return results


def main():
    queries = ["job board", "careers site"]
    all_items: List[Dict] = []
    for q in queries:
        try:
            items = run_search(q.replace(" ", "+"))
        except Exception as e:
            print("Playwright run failed:", e)
            continue
        for it in items:
            it.setdefault("query", q)
        all_items.extend(items)

    out = Path("sample_headless_results.json")
    out.write_text(json.dumps(all_items, indent=2, ensure_ascii=False))
    print(f"Saved {len(all_items)} results to {out}")


if __name__ == "__main__":
    main()
