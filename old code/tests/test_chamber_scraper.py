import os
import sys
import tempfile
import json
import pathlib
import pandas as pd
import pytest

# ensure repo root is on sys.path for imports when pytest runs
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from chamber_scraper import init_database, get_next_pending_town, mark_town_scraped, append_lead, load_learned_selectors, save_learned_selector, learn_pagination_selector


def test_init_and_next_pending(tmp_path):
    db = tmp_path / "db.xlsx"
    init_database(str(db))
    res = get_next_pending_town(str(db))
    assert res is not None
    idx, row = res
    assert "State" in row
    # mark scraped and ensure next pending moves on
    mark_town_scraped(str(db), idx)
    res2 = get_next_pending_town(str(db))
    assert res2 is not None
    assert res2[0] != idx


def test_append_lead_and_persistence(tmp_path):
    db = tmp_path / "db2.xlsx"
    init_database(str(db))
    lead = {"State": "California", "County": "", "Town": "", "Chamber Name": "CalChamber", "Member Name": "ACME Corp", "Category": "Tech", "Website": "https://acme.example", "Phone": ""}
    append_lead(str(db), lead)
    df_progress = pd.read_excel(str(db), sheet_name="Progress")
    df_leads = pd.read_excel(str(db), sheet_name="Leads")
    assert not df_leads.empty
    assert df_leads.iloc[-1]["Member Name"] == "ACME Corp"


class DummyPage:
    def __init__(self, pages):
        self.pages = pages
        self.current = 0

    def click(self, sel):
        # simulate moving to next page
        if sel == "#mystery":
            self.current = min(self.current + 1, len(self.pages) - 1)

    def wait_for_timeout(self, ms):
        pass


def get_members(page):
    return page.pages[page.current]


def test_learn_pagination_selector(tmp_path):
    pages = [ ["A", "B"], ["C", "D"] ]
    page = DummyPage(pages)
    selectors = [".next", "#mystery"]
    # cleanup any learned
    lf = tmp_path / "learned.json"
    if lf.exists():
        lf.unlink()

    sel = learn_pagination_selector(page, selectors, get_members, context=str(lf))
    # The function should return a selector that advances the page (the mystery one)
    assert sel in selectors

    # saving should have added to global learned file
    save_learned_selector(sel, str(lf), path=str(lf))
    data = load_learned_selectors(str(lf))
    assert str(lf) in data
