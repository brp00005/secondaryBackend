import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

LEARNED_SELECTORS = "learned_selectors.json"


def init_database(path: str) -> None:
    """Create `chamber_database.xlsx` with Progress and Leads sheets if missing.

    Progress columns: State, County, Town, Status
    Leads columns: State, County, Town, Chamber Name, Member Name, Category, Website, Phone
    """
    p = Path(path)
    if p.exists():
        return

    # Minimal default: populate Progress with US states only (counties/towns optional)
    states = [
        "California", "Texas", "New York", "Florida", "Illinois",
    ]

    rows = []
    for st in sorted(states):
        # leave County/Town empty for later population or external datasource
        rows.append({"State": st, "County": "", "Town": "", "Status": "Pending"})

    df_progress = pd.DataFrame(rows, columns=["State", "County", "Town", "Status"])
    df_leads = pd.DataFrame(columns=["State", "County", "Town", "Chamber Name", "Member Name", "Category", "Website", "Phone"])

    # atomic write
    with pd.ExcelWriter(p, engine="openpyxl") as ew:
        df_progress.to_excel(ew, sheet_name="Progress", index=False)
        df_leads.to_excel(ew, sheet_name="Leads", index=False)


def load_workbook_dfs(path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df_progress = pd.read_excel(path, sheet_name="Progress")
    df_leads = pd.read_excel(path, sheet_name="Leads")
    return df_progress, df_leads


def get_next_pending_town(path: str) -> Optional[Tuple[int, Dict]]:
    """Return (row_index, row_dict) of the first Progress row where Status == 'Pending'.

    Row index is the integer position in the DataFrame (0-based). Returns None if none pending.
    """
    df_progress, _ = load_workbook_dfs(path)
    pending = df_progress[df_progress["Status"].astype(str).str.lower() == "pending"]
    if pending.empty:
        return None
    idx = int(pending.index[0])
    row = df_progress.loc[idx].to_dict()
    return idx, row


def mark_town_scraped(path: str, row_idx: int) -> None:
    """Set Progress.Status[row_idx] = 'Scraped' and save workbook atomically."""
    df_progress, df_leads = load_workbook_dfs(path)
    if row_idx not in df_progress.index:
        raise IndexError("row_idx out of range")
    df_progress.at[row_idx, "Status"] = "Scraped"

    # atomic save to temp file then replace
    p = Path(path)
    fd, tmp = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    try:
        with pd.ExcelWriter(tmp, engine="openpyxl") as ew:
            df_progress.to_excel(ew, sheet_name="Progress", index=False)
            df_leads.to_excel(ew, sheet_name="Leads", index=False)
        shutil.move(tmp, str(p))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def append_lead(path: str, lead: Dict) -> None:
    """Append a lead dict to the Leads sheet and save atomically.

    lead keys: State, County, Town, Chamber Name, Member Name, Category, Website, Phone
    """
    df_progress, df_leads = load_workbook_dfs(path)
    df_leads = pd.concat([df_leads, pd.DataFrame([lead])], ignore_index=True)

    # atomic save
    p = Path(path)
    fd, tmp = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    try:
        with pd.ExcelWriter(tmp, engine="openpyxl") as ew:
            df_progress.to_excel(ew, sheet_name="Progress", index=False)
            df_leads.to_excel(ew, sheet_name="Leads", index=False)
        shutil.move(tmp, str(p))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def load_learned_selectors(path: str = LEARNED_SELECTORS) -> Dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_learned_selector(selector: str, context: str, path: str = LEARNED_SELECTORS) -> None:
    data = load_learned_selectors(path)
    data.setdefault(context, [])
    if selector not in data[context]:
        data[context].append(selector)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def learn_pagination_selector(page, candidate_selectors: List[str], get_members_callable, context: str = "default") -> Optional[str]:
    """Try candidate selectors on the provided `page`.

    `page` is expected to have `click(selector)` method and `wait_for_timeout(ms)`.
    `get_members_callable(page)` should return a list of member identifiers (names or urls).

    If a candidate changes the member list compared to the previous page, save and return it.
    This function is synchronous-friendly and testable via mocks.
    """
    try:
        prev = list(get_members_callable(page))
    except Exception:
        prev = []

    for sel in candidate_selectors:
        try:
            # attempt click
            if hasattr(page, "click"):
                page.click(sel)
            elif hasattr(page, "locator"):
                page.locator(sel).click()
            # allow time for DOM to update
            if hasattr(page, "wait_for_timeout"):
                page.wait_for_timeout(500)
            new = list(get_members_callable(page))
            if set(new) != set(prev):
                # learned
                save_learned_selector(sel, context)
                return sel
        except Exception:
            continue
    return None


if __name__ == "__main__":
    # simple CLI to initialize DB
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--db", default="chamber_database.xlsx")
    args = p.parse_args()
    init_database(args.db)
    print(f"Initialized {args.db}")
