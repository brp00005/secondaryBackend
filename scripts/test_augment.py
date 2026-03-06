from openpyxl import Workbook
import sys
from pathlib import Path
# ensure repo root is on sys.path when running this script from scripts/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from crawler import DuckDuckGoJobBoardCrawler
from run import augment_counties_with_chambers

# create a small test workbook with a few Alabama counties
wb = Workbook()
ws = wb.active
ws.title = "Counties"
ws.append(["State", "County"])
for c in ["Chilton", "Choctaw", "Clarke", "Clay", "Cleburne"]:
    ws.append(["Alabama", c])
wb.save("us_counties_test.xlsx")

# create crawler with a higher rate to be polite
crawler = DuckDuckGoJobBoardCrawler(rate_limit=3.0, engine="brave")
augment_counties_with_chambers(crawler, counties_path="us_counties_test.xlsx", output_path="us_counties_test_out.xlsx", max_search_pages=1)
print("Test augmentation completed.")
