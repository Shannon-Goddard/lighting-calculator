# CI Lighting — Grow Light Comparison Dataset

An open dataset of **132 LED grow lights** across **10 brands**, built for home growers who want to make informed purchasing decisions based on real specs — not marketing.

>All data and code provided in this repository is licensed under Creative Commons Attribution 4.0 International. © 2026 Loyal9 LLC.

## Datasets

### `lighting-data.csv` / `lighting-data.json`

Raw manufacturer specifications. Every value comes directly from product pages, spec sheets, or PDF datasheets. Nothing calculated, nothing assumed.

**44 columns** including: PPF, efficacy, wattage, flowering/veg footprints, mounting heights, dimensions, weight, lifespan, warranty, certifications, price, and product URLs.

### `lighting-data-complete.csv` / `lighting-data-complete.json`

Enriched version with safe defaults and calculated fields applied. Use this if you want a more complete dataset ready for analysis or app development.

**41 columns** (intensity columns removed due to <7% data availability) plus calculated/default values filled for 547 cells.

### `strain-index.json`

A slim strain database for powering the grow cost calculator's strain selector. **8,744 strains** with flowering time data.

**Fields:** `name`, `flower_days`, `auto` (boolean), `logo` (path or null)

**Sources:**
- [CI Strains](https://poweredbyci.live) — 21,000+ strains with 53 columns including precise flowering day ranges. Used as the primary source for `flowering_days_avg`.
- [GrowApp](https://poweredbyci.live) — 2,883 strains with logos. Overlaid onto CI data to add strain imagery.

**How it was built:**
1. Loaded CI Strains (12,438 unique names after deduplication)
2. Merged GrowApp strains — matched 1,386 to existing CI entries (added logos), added 1,492 GrowApp-only strains (flower weeks × 7 = days)
3. Combined total: 13,930 unique strains
4. Filtered to only strains with `flower_days` populated — removed 5,186 without flowering time data (pointless for a calculator)
5. Final: **8,744 strains**, 2,878 with logos

**Logo fallback:** Strains without a logo use a random default image (`img/strains/default-1.png` through `default-10.png`).

## Brands Covered

| Brand | Products |
|-------|----------|
| Horticulture Lighting Group (HLG) | 22 |
| AC Infinity | 18 |
| Spider Farmer | 18 |
| Vivosun | 18 |
| Mars Hydro | 17 |
| California Lightworks | 16 |
| Photontek | 14 |
| Grower's Choice | 10 |
| Mammoth Lighting | 6 |
| Gavita | 3 |

## Calculated Fields & Defaults (Complete Dataset)

### Safe Defaults

| Column | Default | Rationale |
|--------|---------|-----------|
| `Hz_low` | 50 | Standard for any LED driver rated 100–277VAC |
| `Hz_high` | 60 | Standard for any LED driver rated 100–277VAC |
| `Thermal Management` | Passive | All LED grow lights in this dataset use passive cooling (heat sinks, no fans) |
| `max_ambient_temperature_c` | 40 | Industry standard max operating temp for passive LED fixtures |
| `max_ambient_temperature_f` | 104 | Conversion of 40°C |

### Mounting Heights

Source: [GrowWeedEasy — How Far Away Should Grow Lights Be?](https://www.growweedeasy.com/how-far-grow-lights)

| Growth Stage | Distance from Canopy |
|---|---|
| Seedling | 24–36 inches |
| Vegetative | 18–24 inches |
| Flowering | 12–18 inches |

### Veg Footprint Estimation

`veg_footprint = flowering_footprint + 1ft` per dimension.

During veg, lights are mounted higher (18–24" vs 12–18"), spreading light over a wider area. The +1ft per side is a conservative estimate matching how manufacturers who publish both values typically differ.

### Thermal Management Normalization

Inconsistent values across brands were normalized:
- "Passive-Cooled" → "Passive"
- "Passive-Cooled Design" → "Passive"
- "Passive Heat Sink" → "Passive"

## Useful Calculated Metrics

These aren't in the dataset but are easy to derive and important for comparison:

### Watts per Square Foot (Flowering)

```
wattage_per_sqft = max_Watts / (flowering_footprint_length_ft × flowering_footprint_width_ft)
```

**Why it matters:** This is the #1 metric growers use to compare lights of different sizes. A 600W light covering 5×5 (24 W/sqft) isn't necessarily better than a 200W light covering 3×3 (22 W/sqft). It normalizes power to coverage area so you're comparing apples to apples. Target: 30–50 W/sqft for flowering.

### Price per Watt

```
price_per_watt = price / max_Watts
```

**Why it matters:** Strips away the "bigger light = more expensive" noise. A $800 600W light ($1.33/W) vs a $300 200W light ($1.50/W) — the bigger light is actually better value per watt. Helps budget-conscious growers find the sweet spot.

### Cost per Grow Cycle

```
daily_kwh = (max_Watts × hours_per_day) / 1000
cycle_cost = daily_kwh × days_in_cycle × electric_rate
```

**Why it matters:** The sticker price is only part of the cost. A cheap light with poor efficacy can cost more in electricity over a single grow than the price difference to a premium light. This metric shows the true operating cost.

## Scripts

### `fill_defaults.py`

Fills safe defaults and calculated fields into `lighting-data-complete.csv`. Idempotent — won't overwrite existing values.

```bash
python fill_defaults.py
```

### `export_json.py`

Converts both CSV datasets to JSON format.

```bash
python export_json.py
```

### `parse_spec.py`

The original HLG parser for copy/pasted PDF spec text. Kept as reference for the parsing approach used across all brands.

## Data Freshness

The `data_timestamp` column in the complete dataset indicates when prices and specs were last verified. Current data as of: **2026-07-07**.

## Known Gaps

| Column | Missing | Notes |
|--------|---------|-------|
| PPF | 34/132 | Not published by all manufacturers |
| efficacy | 32/132 | Same as PPF |
| flowering_footprint | 34/132 | Some brands don't spec coverage area |
| weight_lb | 44/132 | Not always on spec sheets |
| Warranty_years | 45/132 | Varies, some brands list on separate pages |

## Credits

This dataset was built collaboratively by a human researcher and [Amazon Q Developer](https://aws.amazon.com/q/developer/), an AI coding assistant by AWS.

**Human:** Product research, spec sourcing, data verification, and domain expertise on grow light performance.

**Amazon Q Developer:** Parser development (10 brand-specific parsers for wildly different formats), data pipeline scripts, schema design, missing data analysis, safe default logic, and documentation.

## Limitations

This dataset is provided for informational and educational purposes. Product specifications belong to their respective manufacturers. Prices are subject to change.
