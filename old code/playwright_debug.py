from pathlib import Path
try:
    from playwright.sync_api import sync_playwright
except Exception as e:
    print("Playwright import failed:", e)
    raise

def main():
    q = "job+board"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://duckduckgo.com/?q={q}")
        page.wait_for_timeout(2000)
        html = page.content()
        Path("ddg_playwright.html").write_text(html, encoding="utf-8")
        print("Wrote ddg_playwright.html")
        browser.close()

if __name__ == '__main__':
    main()
