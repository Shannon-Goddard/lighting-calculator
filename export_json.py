"""
export_json.py — Convert CSV datasets to JSON format.
Usage: python export_json.py
"""

import csv, json
from pathlib import Path

def csv_to_json(csv_path, json_path):
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2)
    print(f"  {json_path.name}: {len(rows)} products")

print("Exporting JSON:")
csv_to_json(Path("lighting-data.csv"), Path("lighting-data.json"))
csv_to_json(Path("lighting-data-complete.csv"), Path("lighting-data-complete.json"))
print("Done.")
