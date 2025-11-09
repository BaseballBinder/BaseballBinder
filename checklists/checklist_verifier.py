import pandas as pd
import json
from pathlib import Path
import re

BASE_PATH = Path(__file__).parent  # the checklists folder itself

def parse_filename(filename: str):
    """Extract year and set name from filename like '2023 Topps Update Series.csv'"""
    match = re.match(r"(\d{4})\s*(.*)\.csv", filename)
    if match:
        year = match.group(1)
        set_name = match.group(2).replace("_", " ").strip()
    else:
        year = "Unknown"
        set_name = filename.replace(".csv", "")
    return year, set_name


def verify_checklist(csv_path: Path):
    print(f"\n--- Checking {csv_path.name} ---")

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"❌ Could not read {csv_path.name}: {e}")
        return

    if "Variety" not in df.columns:
        print("⚠ No 'Variety' column found. Skipping file.")
        return

    varieties = sorted(df["Variety"].dropna().unique())
    meta_path = csv_path.with_suffix(".json")

    # Extract metadata from filename
    year, set_name = parse_filename(csv_path.name)

    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
    else:
        meta = {
            "set_name": set_name,
            "year": year,
            "variety_counts": {},
            "verified": False
        }

    # Ask for any missing variety totals
    for v in varieties:
        if v not in meta["variety_counts"]:
            count = input(f"⚠ Enter number of cards for variety '{v}' in {set_name} ({year}): ")
            try:
                meta["variety_counts"][v] = int(count)
            except ValueError:
                print("Invalid number, skipping this variety.")

    meta["verified"] = all(isinstance(n, int) for n in meta["variety_counts"].values())

    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"✅ Metadata updated: {meta_path.name}")
    if meta["verified"]:
        print("✅ All varieties complete — file verified!")
    else:
        print("⚠ Missing data — file not fully verified.")


def main():
    print("📋 Starting checklist verification...")
    for csv_file in BASE_PATH.glob("*.csv"):
        verify_checklist(csv_file)
    print("\n✅ Verification complete.")


if __name__ == "__main__":
    main()
