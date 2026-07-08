import csv
import re
import sys
import os

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lighting.csv")


def parse_spec(text):
    """Parse spec text into a dict matching CSV columns."""
    # Normalize unicode quotes/marks to ASCII
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2032", "'").replace("\u2033", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")

    data = {}

    # Metadata fields (optional, can be in the text)
    m = re.search(r"^dba\s+(.+)", text, re.MULTILINE)
    data["dba"] = m.group(1).strip() if m else ""
    m = re.search(r"^make\s+(.+)", text, re.MULTILINE)
    data["make"] = m.group(1).strip() if m else ""
    m = re.search(r"^model\s+(.+)", text, re.MULTILINE)
    data["model"] = m.group(1).strip() if m else ""
    m = re.search(r"^pdf\s+(.+)", text, re.MULTILINE)
    data["pdf"] = m.group(1).strip() if m else ""

    # Type - first line that isn't a known key
    known_keys = r"^(dba|make|model|pdf|PPF|Input|Efficacy|Voltage|Power|Flowering|Flower|Veg|Recommended|Thermal|Max|Dimm|Dimensions|Weight|Warranty|Certifications|Temperature|Lifespan|Propagation)\b"
    for line in text.strip().splitlines():
        line = line.strip()
        if line and not re.match(known_keys, line, re.IGNORECASE):
            data["type"] = line
            break
    else:
        data["type"] = ""

    # PPF (strip trailing +)
    m = re.search(r"PPF\s+([\d.]+)", text)
    data["PPF"] = m.group(1) if m else ""

    # Efficacy
    m = re.search(r"Efficacy\s+([\d.]+)", text)
    data["efficacy_umol_joule"] = m.group(1) if m else ""

    # Voltage / Hz - handles colon, comma, or just whitespace between VAC and Hz
    m = re.search(r"(\d+)\s*VAC\s*-\s*(\d+)\s*VAC\s*[,:;\s]\s*(\d+)[-/](\d+)\s*Hz", text, re.IGNORECASE)
    if m:
        data["VAC_low"], data["VAC_high"] = m.group(1), m.group(2)
        data["Hz_low"], data["Hz_high"] = m.group(3), m.group(4)
    else:
        # Try without Hz (just VAC range)
        m = re.search(r"(\d+)\s*VAC\s*-\s*(\d+)\s*VAC", text, re.IGNORECASE)
        if m:
            data["VAC_low"], data["VAC_high"] = m.group(1), m.group(2)
        else:
            data["VAC_low"] = data["VAC_high"] = ""
        data["Hz_low"] = data["Hz_high"] = ""

    # Power (max watts) - handles "0-650 Watts", "100-210 Watts", or "95 Watts"
    m = re.search(r"Power\s+(?:\d+-)?(\d+)\s*Watts", text, re.IGNORECASE)
    data["max_Watts"] = m.group(1) if m else ""

    # --- Footprints ---
    data["flowering_footprint_length_ft"] = ""
    data["flowering_footprint_width_ft"] = ""
    data["flowering_mounting_height_min_inches"] = ""
    data["flowering_mounting_height_max_inches"] = ""
    data["veg_footprint_length_ft"] = ""
    data["veg_footprint_width_ft"] = ""
    data["veg_mounting_height_min_inches"] = ""
    data["veg_mounting_height_max_inches"] = ""
    data["propagation_mounting_height_min_inches"] = ""
    data["propagation_mounting_height_max_inches"] = ""

    # Find the footprint line(s)
    fp_line = re.search(r"(?:Flowering|Flower)\.?\s+Footprint\s+(.+)", text, re.IGNORECASE)
    if fp_line:
        fp_text = fp_line.group(1)
        # Check for veg on same line first: "5' x 5' Veg" or "7' x 7' for Veg"
        vm = re.search(r"([\d.]+)['\".\s]*[Xx]\s*([\d.]+)['\".\s]*(?:for\s+)?Veg", fp_text, re.IGNORECASE)
        if vm:
            data["veg_footprint_length_ft"] = vm.group(1)
            data["veg_footprint_width_ft"] = vm.group(2)
            # Remove the veg part to isolate flowering
            flower_part = fp_text[:vm.start()]
        else:
            flower_part = fp_text
        # Find all dimension pairs in the flowering part
        flower_dims = re.findall(r"([\d.]+)['\".\s]*[Xx]\s*([\d.]+)", flower_part)
        if flower_dims:
            # Use the last one (largest option)
            data["flowering_footprint_length_ft"] = flower_dims[-1][0]
            data["flowering_footprint_width_ft"] = flower_dims[-1][1]
        # Check for "at height" in flowering part
        fh = re.search(r"(?:at|@)\s*(\d+)[\"'\s]*[-to]+\s*(\d+)", flower_part)
        if fh:
            data["flowering_mounting_height_min_inches"] = fh.group(1)
            data["flowering_mounting_height_max_inches"] = fh.group(2)

    # Separate "Veg Footprint" line
    vfp_line = re.search(r"Veg\s+Footprint\s+([\d.]+)['\".\s]*[Xx]\s*([\d.]+)(?:['\".\s]*(?:at|@)\s*(\d+)[\"'\s]*[-to]+\s*(\d+))?", text, re.IGNORECASE)
    if vfp_line:
        data["veg_footprint_length_ft"] = vfp_line.group(1)
        data["veg_footprint_width_ft"] = vfp_line.group(2)
        if vfp_line.group(3):
            data["veg_mounting_height_min_inches"] = vfp_line.group(3)
        if vfp_line.group(4):
            data["veg_mounting_height_max_inches"] = vfp_line.group(4)

    # --- Mounting heights from a separate "Recommended height" line ---
    height_match = re.search(r"[Rr]ecommended.*?height.*?canopy[\s]+(.*?)(?=\n[A-Z]|\n[a-z]|$)", text, re.IGNORECASE | re.DOTALL)
    if height_match:
        htext = height_match.group(1).replace("\n", " ").replace("\r", " ").strip()
        # Flower height: "16" - 20" Flower" or "15" Flower" or "24" Flowering"
        fm = re.search(r"(\d+)[\"'\s]*(?:[-to]+\s*(\d+)[\"'\s]*)?(?:Flower(?:ing)?)", htext, re.IGNORECASE)
        if fm and not data["flowering_mounting_height_min_inches"]:
            data["flowering_mounting_height_min_inches"] = fm.group(1)
            data["flowering_mounting_height_max_inches"] = fm.group(2) if fm.group(2) else fm.group(1)
        # Veg height: "24" Veg" or "24" for Veg"
        vm = re.search(r"(\d+)[\"'\s]*(?:[-xXto]+\s*(\d+)[\"'\s]*)?(?:for\s+)?Veg", htext, re.IGNORECASE)
        if vm and not data["veg_mounting_height_min_inches"]:
            data["veg_mounting_height_min_inches"] = vm.group(1)
            data["veg_mounting_height_max_inches"] = vm.group(2) if vm.group(2) else vm.group(1)
        # Simple single height (no Flower/Veg label)
        if not fm and not vm:
            # Try range first: "18" - 24""
            sm = re.search(r"(\d+)[\"'\s]*[-to]+\s*(\d+)", htext)
            if sm:
                if data["flowering_footprint_length_ft"] and not data["flowering_mounting_height_min_inches"]:
                    data["flowering_mounting_height_min_inches"] = sm.group(1)
                    data["flowering_mounting_height_max_inches"] = sm.group(2)
                elif data["veg_footprint_length_ft"] and not data["veg_mounting_height_min_inches"]:
                    data["veg_mounting_height_min_inches"] = sm.group(1)
                    data["veg_mounting_height_max_inches"] = sm.group(2)
            else:
                # Single value: "18""
                sv = re.search(r"(\d+)", htext)
                if sv:
                    if data["flowering_footprint_length_ft"] and not data["flowering_mounting_height_min_inches"]:
                        data["flowering_mounting_height_min_inches"] = sv.group(1)
                        data["flowering_mounting_height_max_inches"] = sv.group(1)
                    elif data["veg_footprint_length_ft"] and not data["veg_mounting_height_min_inches"]:
                        data["veg_mounting_height_min_inches"] = sv.group(1)
                        data["veg_mounting_height_max_inches"] = sv.group(1)

    # Propagation height
    m = re.search(r"Propagation.*?height.*?(\d+)[\"'\s]*[-to]+\s*(\d+)", text, re.IGNORECASE)
    if m:
        data["propagation_mounting_height_min_inches"] = m.group(1)
        data["propagation_mounting_height_max_inches"] = m.group(2)
    else:
        m = re.search(r"Propagation.*?height.*?(\d+)", text, re.IGNORECASE)
        if m:
            data["propagation_mounting_height_min_inches"] = m.group(1)
            data["propagation_mounting_height_max_inches"] = m.group(1)

    # --- Intensity percentages ---
    data["propagation_intensity_pct_min"] = ""
    data["propagation_intensity_pct_max"] = ""
    data["veg_intensity_pct_min"] = ""
    data["veg_intensity_pct_max"] = ""
    data["flower_intensity_pct_min"] = ""
    data["flower_intensity_pct_max"] = ""

    # Propagation intensity
    m = re.search(r"Propagation.*?[Ii]ntensity[:\s]*(\d+)[%\s]*[-to]*\s*(\d+)?%?", text, re.IGNORECASE)
    if m:
        data["propagation_intensity_pct_min"] = m.group(1)
        data["propagation_intensity_pct_max"] = m.group(2) if m.group(2) else m.group(1)

    # Veg intensity
    m = re.search(r"Veg.*?[Ii]ntensity[:\s]*(\d+)[%\s]*[-to]*\s*(\d+)?%?", text, re.IGNORECASE)
    if m:
        data["veg_intensity_pct_min"] = m.group(1)
        data["veg_intensity_pct_max"] = m.group(2) if m.group(2) else m.group(1)

    # Flower intensity
    m = re.search(r"Flow(?:er(?:ing)?|r).*?[Ii]ntensity[:\s]*(\d+)[%\s]*[-to]*\s*(\d+)?%?", text, re.IGNORECASE)
    if m:
        data["flower_intensity_pct_min"] = m.group(1)
        data["flower_intensity_pct_max"] = m.group(2) if m.group(2) else m.group(1)

    # Thermal Management
    m = re.search(r"Thermal Management\s+(.+)", text)
    data["Thermal Management"] = m.group(1).strip() if m else ""

    # Max Ambient Temperature - handles "40C (104F)", "32.22C (90F)", "40 °C (104 °F)"
    m = re.search(r"(?:Max Ambient )?Temperature\s+([\d.]+)\s*(?:\u00b0\s*)?C\s*\(([\d.]+)\s*(?:\u00b0\s*)?F\)", text)
    if m:
        data["max_ambient_temperature_c"] = m.group(1)
        data["max_ambient_temperature_f"] = m.group(2)
    else:
        data["max_ambient_temperature_c"] = data["max_ambient_temperature_f"] = ""

    # Dimming - handles "Dimming Options ...", "Dimmable Options ...", or "Dimmable ..."
    m = re.search(r"Dimm(?:ing|able)\s+Options\s+(.+)", text, re.IGNORECASE)
    if m:
        data["dimmable"] = "TRUE"
        data["Dimming Options"] = m.group(1).strip()
    else:
        m = re.search(r"Dimmable\s+(.+)", text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if val.lower() in ("no", "false"):
                data["dimmable"] = "FALSE"
                data["Dimming Options"] = ""
            else:
                data["dimmable"] = "TRUE"
                data["Dimming Options"] = val
        else:
            data["dimmable"] = "FALSE"
            data["Dimming Options"] = ""

    # Dimensions
    m = re.search(r"Dimensions\s+([\d.]+)[\"'\s]*[Xx]\s*([\d.]+)[\"'\s]*[Xx]\s*([\d.]+)", text)
    if m:
        data["dimensions_length_inches"] = m.group(1)
        data["dimensions_width_inches"] = m.group(2)
        data["dimensions_height_inches"] = m.group(3)
    else:
        data["dimensions_length_inches"] = data["dimensions_width_inches"] = data["dimensions_height_inches"] = ""

    # Weight
    m = re.search(r"Weight\s+([\d.]+)\s*(?:lbs?|pounds?)", text, re.IGNORECASE)
    data["weight_lb"] = m.group(1) if m else ""

    # Lifespan
    m = re.search(r"Lifespan\s+(.+)", text, re.IGNORECASE)
    data["lifespan_hours"] = m.group(1).strip() if m else ""

    # Warranty
    m = re.search(r"Warranty\s+(\d+)", text)
    data["Warranty_years"] = m.group(1) if m else ""

    # Certifications
    m = re.search(r"Certifications\s+(.+)", text)
    data["Certifications"] = m.group(1).strip() if m else ""

    return data


def next_index(csv_path):
    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        indices = [int(row["index"]) for row in reader if row["index"].isdigit()]
    return f"{max(indices) + 1:05d}" if indices else "00001"


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_spec.py <spec_text_file>")
        print("  e.g. python parse_spec.py chat.txt")
        sys.exit(1)

    spec_file = sys.argv[1]

    with open(spec_file, "r", encoding="utf-8") as f:
        text = f.read()

    data = parse_spec(text)

    dba = data.get("dba", "")
    make = data.get("make", "")
    model = data.get("model", "")
    pdf = data.get("pdf", "")
    make_slug = make.lower().replace(" ", "_") if make else ""
    model_slug = model.lower().replace(" ", "_") if model else ""

    idx = next_index(CSV_PATH)

    row = {
        "index": idx,
        "dba": dba,
        "make": make,
        "make_slug": make_slug,
        "model": model,
        "model_slug": model_slug,
        "type": data["type"],
        "PPF": data["PPF"],
        "efficacy_umol_joule": data["efficacy_umol_joule"],
        "Hz_low": data["Hz_low"],
        "Hz_high": data["Hz_high"],
        "VAC_low": data["VAC_low"],
        "VAC_high": data["VAC_high"],
        "max_Watts": data["max_Watts"],
        "flowering_footprint_length_ft": data["flowering_footprint_length_ft"],
        "flowering_footprint_width_ft": data["flowering_footprint_width_ft"],
        "veg_footprint_length_ft": data["veg_footprint_length_ft"],
        "veg_footprint_width_ft": data["veg_footprint_width_ft"],
        "flowering_mounting_height_min_inches": data["flowering_mounting_height_min_inches"],
        "flowering_mounting_height_max_inches": data["flowering_mounting_height_max_inches"],
        "veg_mounting_height_min_inches": data["veg_mounting_height_min_inches"],
        "veg_mounting_height_max_inches": data["veg_mounting_height_max_inches"],
        "propagation_mounting_height_min_inches": data["propagation_mounting_height_min_inches"],
        "propagation_mounting_height_max_inches": data["propagation_mounting_height_max_inches"],
        "propagation_intensity_pct_min": data["propagation_intensity_pct_min"],
        "propagation_intensity_pct_max": data["propagation_intensity_pct_max"],
        "veg_intensity_pct_min": data["veg_intensity_pct_min"],
        "veg_intensity_pct_max": data["veg_intensity_pct_max"],
        "flower_intensity_pct_min": data["flower_intensity_pct_min"],
        "flower_intensity_pct_max": data["flower_intensity_pct_max"],
        "Thermal Management": data["Thermal Management"],
        "max_ambient_temperature_c": data["max_ambient_temperature_c"],
        "max_ambient_temperature_f": data["max_ambient_temperature_f"],
        "dimmable": data["dimmable"],
        "Dimming Options": data["Dimming Options"],
        "dimensions_length_inches": data["dimensions_length_inches"],
        "dimensions_width_inches": data["dimensions_width_inches"],
        "dimensions_height_inches": data["dimensions_height_inches"],
        "weight_lb": data["weight_lb"],
        "lifespan_hours": data["lifespan_hours"],
        "Warranty_years": data["Warranty_years"],
        "Certifications": data["Certifications"],
        "pdf": pdf,
    }

    # Read existing headers
    with open(CSV_PATH, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

    with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(row)

    print(f"Added row {idx}: {make} {model}")


if __name__ == "__main__":
    main()
