# scripts/merge_fragments.py
"""
Merge CSV fragments produced by the PDF extractor (data_raw/) into one CSV per logical table type (Option B).
Saves outputs into data_cleaned/:
 - arrivals_by_nationality.csv
 - arrivals_by_residence.csv
 - facility_arrivals.csv
 - atoll_distribution.csv
 - key_indicators.csv
 - bed_capacity.csv
 - bed_nights_occupancy.csv
 - establishments.csv
 - other.csv
Also writes fragment_assignment_index.txt describing which fragment went to which category.
"""

import re
from pathlib import Path
import pandas as pd

# --- config: change paths if your repo differs ---
DATA_RAW = Path("data_raw")          # where extractor saved fragments
OUT_DIR = Path("data_cleaned")      # where merged outputs will be saved
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- classification rules (heuristic) ---
rules = [
    ("arrivals_by_nationality", ["nationality", "country of nationality", "arrivals by nationality", "country", "citizenship"]),
    ("arrivals_by_residence", ["country of residence", "residence", "residents", "residence country"]),
    ("facility_arrivals", ["resort", "guesthouse", "hotel", "vessel", "facility", "arrival distribution to tourist facilities"]),
    ("atoll_distribution", ["atoll", "arrivals to atolls", "atoll distribution", "kaafu", "raa", "baa"]),
    ("key_indicators", ["total arrivals", "occupancy", "bed nights", "average duration", "airport", "male", "female", "by air", "by sea", "key indicators"]),
    ("bed_capacity", ["bed capacity", "beds in operation", "total beds", "registered beds", "operational beds"]),
    ("bed_nights_occupancy", ["bed nights", "occupancy rate", "bed nights & occupancy", "bed nights & occupancy rate"]),
    ("establishments", ["registered", "operational", "establishments", "registered establishments", "operational establishments"]),
    ("other", ["notes", "source", "table", "page"]),
]

# utility functions
def text_matches(text):
    t = text.lower()
    for target, kws in rules:
        for kw in kws:
            if kw in t:
                return target
    return None

def safe_read_csv(path):
    # try utf-8 then latin1
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception:
        try:
            return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="latin1")
        except Exception:
            return None

def year_month_from_name(name):
    # Accepts names like "2025_January_table3.csv" or "January 2025_table1.csv"
    m = re.match(r"(\d{4})[_\s-]+([A-Za-z]+)", name)
    if m:
        return int(m.group(1)), m.group(2)
    m2 = re.match(r"([A-Za-z]+)[_\s-]+(\d{4})", name)
    if m2:
        return int(m2.group(2)), m2.group(1)
    return None, None

# collect CSVs
csv_files = sorted([p for p in DATA_RAW.glob("*.csv") if p.is_file()])
print(f"Found {len(csv_files)} CSV fragments in {DATA_RAW}")

assigned = {name: [] for name, _ in rules}
assigned["unknown"] = []

for path in csv_files:
    df = safe_read_csv(path)
    if df is None:
        assigned["unknown"].append((path, None))
        continue

    header = " ".join(list(df.columns.astype(str)))
    preview_rows_series = df.head(3).astype(str).apply(lambda row: " ".join(row.values.astype(str)), axis=1)
    preview_rows = " ".join(list(preview_rows_series))

    preview = (header + " " + preview_rows).strip().lower()

    nrows, ncols = df.shape
    numeric_cells = sum(1 for v in df.values.flatten() if isinstance(v, str) and re.search(r"\d", v))
    numeric_density = numeric_cells / max(1, nrows * max(1, ncols))

    match = text_matches(preview)
    if match is None:
        # fallback heuristics
        if nrows >= 50 and numeric_density > 0.2:
            match = "arrivals_by_nationality"
        elif nrows >= 15 and "atoll" in preview:
            match = "atoll_distribution"
        elif "bed nights" in preview or "occupancy" in preview:
            match = "bed_nights_occupancy"
        elif any(k in preview for k in ["resort", "hotel", "guesthouse"]):
            match = "facility_arrivals"
        elif any(k in preview for k in ["registered", "operational"]):
            match = "establishments"
        elif any(k in preview for k in ["beds", "bed"]):
            match = "bed_capacity"
        else:
            match = "unknown"

    assigned[match].append((path, df))

# Merge fragments per category and save one CSV per category (Option B)
final_dfs = {}
for category, items in assigned.items():
    rows = []
    for path, df in items:
        if df is None:
            continue
        year, month = year_month_from_name(path.name)
        df2 = df.copy()
        # add provenance metadata
        df2.insert(0, "_source_file", path.name)
        df2.insert(0, "month", month if month is not None else "")
        df2.insert(0, "year", year if year is not None else "")
        rows.append(df2)
    if rows:
        concat_df = pd.concat(rows, ignore_index=True, sort=False)
        final_dfs[category] = concat_df

# Save merged files
saved = []
for category, df in final_dfs.items():
    out_path = OUT_DIR / f"{category}.csv"
    if "year" not in df.columns:
        df.insert(0, "year", "")
    if "month" not in df.columns:
        df.insert(1, "month", "")
    df.to_csv(out_path, index=False)
    saved.append(out_path.name)
    print(f"Saved: {out_path} ({df.shape[0]} rows x {df.shape[1]} cols)")

# write index mapping
idx_path = OUT_DIR / "fragment_assignment_index.txt"
with open(idx_path, "w", encoding="utf-8") as fh:
    for category, items in assigned.items():
        for path, df in items:
            fh.write(f"{path.name}\t{category}\trows={df.shape[0] if df is not None else 'NA'}\tcols={df.shape[1] if df is not None else 'NA'}\n")

print("Index saved to", idx_path)
print("Done. Produced files:", saved)