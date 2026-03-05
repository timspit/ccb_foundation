#!/usr/bin/env python3
"""
Geocode recovery service providers by ZIP code centroid.

Adds latitude/longitude columns to recovery_services.csv.
Run this script whenever new providers are added to the dataset.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pgeocode

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import DATA_DIR


def geocode_providers():
    input_file = DATA_DIR / "recovery_services.csv"

    if not input_file.exists():
        print(f"Error: {input_file} not found. Run combine_data.py first.")
        return

    df = pd.read_csv(input_file, dtype={"zip_code": str})

    # Zero-pad ZIP codes to 5 digits (MA zips start with 0)
    df["zip_code"] = df["zip_code"].str.strip().str.zfill(5)

    # Initialize lat/lng columns if not present
    if "latitude" not in df.columns:
        df["latitude"] = np.nan
    if "longitude" not in df.columns:
        df["longitude"] = np.nan

    nomi = pgeocode.Nominatim("us")

    # Only geocode rows missing coordinates
    mask = df["latitude"].isna() | df["longitude"].isna()
    unique_zips = df.loc[mask, "zip_code"].dropna().unique()

    print(f"Geocoding {len(unique_zips)} unique ZIP codes for {mask.sum()} providers...")

    zip_cache = {}
    for zip_code in unique_zips:
        if len(zip_code) == 5 and zip_code.isdigit():
            result = nomi.query_postal_code(zip_code)
            if not pd.isna(result.latitude) and not pd.isna(result.longitude):
                zip_cache[zip_code] = (float(result.latitude), float(result.longitude))
            else:
                print(f"  Could not geocode ZIP: {zip_code}")

    for zip_code, (lat, lng) in zip_cache.items():
        idx = df["zip_code"] == zip_code
        df.loc[idx, "latitude"] = lat
        df.loc[idx, "longitude"] = lng

    geocoded = int(df["latitude"].notna().sum())
    print(f"Geocoded {geocoded}/{len(df)} providers")

    df.to_csv(input_file, index=False)
    print(f"Saved to {input_file}")


if __name__ == "__main__":
    geocode_providers()
