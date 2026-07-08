"""
fill_defaults.py — Fill missing data in lighting-data-complete.csv using safe defaults and calculations.

Logic documented in README.md. Sources:
- Hz: Standard for any 100-277V LED driver is 50/60 Hz
- Thermal Management: All LED grow lights in this dataset are passively cooled
- Max ambient temp: Industry standard 40°C / 104°F for passive LED fixtures
- Mounting heights: https://www.growweedeasy.com/how-far-grow-lights
    Seedling: 24-36", Veg: 18-24", Flowering: 12-18"
- Veg footprint: flowering footprint + 1ft each dimension (light spreads wider at veg height)
"""

import csv
from pathlib import Path

CSV_PATH = Path(__file__).parent / "lighting-data-complete.csv"

# Read
with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

changes = {
    "Hz_low": 0, "Hz_high": 0,
    "Thermal Management": 0,
    "max_ambient_temperature_c": 0, "max_ambient_temperature_f": 0,
    "flowering_mounting_height_min_inches": 0, "flowering_mounting_height_max_inches": 0,
    "veg_mounting_height_min_inches": 0, "veg_mounting_height_max_inches": 0,
    "veg_footprint_length_ft": 0, "veg_footprint_width_ft": 0,
}

for row in rows:
    # Hz: fill 50/60 if VAC columns are populated
    if not row["Hz_low"] and row["VAC_low"]:
        row["Hz_low"] = "50"
        changes["Hz_low"] += 1
    if not row["Hz_high"] and row["VAC_high"]:
        row["Hz_high"] = "60"
        changes["Hz_high"] += 1

    # Thermal Management: normalize existing + fill empty
    if not row["Thermal Management"]:
        row["Thermal Management"] = "Passive"
        changes["Thermal Management"] += 1
    elif row["Thermal Management"] in ("Passive-Cooled", "Passive-Cooled Design", "Passive Heat Sink"):
        row["Thermal Management"] = "Passive"

    # Max ambient temp: 40C/104F for passive-cooled
    if not row["max_ambient_temperature_c"]:
        row["max_ambient_temperature_c"] = "40"
        row["max_ambient_temperature_f"] = "104"
        changes["max_ambient_temperature_c"] += 1

    # Mounting heights from growweedeasy.com reference
    if not row["flowering_mounting_height_min_inches"]:
        row["flowering_mounting_height_min_inches"] = "12"
        row["flowering_mounting_height_max_inches"] = "18"
        changes["flowering_mounting_height_min_inches"] += 1
    if not row["veg_mounting_height_min_inches"]:
        row["veg_mounting_height_min_inches"] = "18"
        row["veg_mounting_height_max_inches"] = "24"
        changes["veg_mounting_height_min_inches"] += 1

    # Veg footprint: flowering + 1ft each dimension
    if not row["veg_footprint_length_ft"] and row["flowering_footprint_length_ft"]:
        try:
            fl = float(row["flowering_footprint_length_ft"])
            fw = float(row["flowering_footprint_width_ft"])
            row["veg_footprint_length_ft"] = str(fl + 1)
            row["veg_footprint_width_ft"] = str(fw + 1)
            changes["veg_footprint_length_ft"] += 1
        except (ValueError, TypeError):
            pass

# Write
with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Cells filled:")
for col, count in changes.items():
    if count:
        print(f"  {col}: {count}")
print(f"\nTotal cells filled: {sum(changes.values())}")
