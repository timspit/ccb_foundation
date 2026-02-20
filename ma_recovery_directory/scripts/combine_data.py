#!/usr/bin/env python3
"""
Combine data from different sources into a single dataset
"""

import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import DATA_DIR


def combine_datasets():
    """Combine BSAS and Peer Recovery data"""

    all_data = []

    # Load BSAS data
    bsas_file = DATA_DIR / "bsas_providers.csv"
    if bsas_file.exists():
        print(f"Loading BSAS data from {bsas_file}")
        bsas_df = pd.read_csv(bsas_file)

        # Standardize columns
        bsas_standardized = pd.DataFrame({
            'name': bsas_df['name'],
            'address': bsas_df['address'],
            'city': bsas_df['city'],
            'state': bsas_df['state'],
            'zip_code': bsas_df['zip_code'],
            'phone': bsas_df['phone'],
            'email': '',
            'website': bsas_df.get('website', ''),
            'service_types': bsas_df.get('service_setting', ''),
            'hours': '',
            'populations_served': '',
            'languages': 'English',
            'eligibility': '',
            'payment_options': '',
            'data_source': 'BSAS'
        })

        all_data.append(bsas_standardized)
        print(f"Loaded {len(bsas_standardized)} BSAS providers")

    # Load Peer Recovery data
    peer_file = DATA_DIR / "peer_recovery_centers.csv"
    if peer_file.exists():
        print(f"Loading Peer Recovery data from {peer_file}")
        peer_df = pd.read_csv(peer_file)

        # Standardize columns
        peer_standardized = pd.DataFrame({
            'name': peer_df['name'],
            'address': peer_df['address'],
            'city': peer_df['city'],
            'state': peer_df['state'],
            'zip_code': peer_df['zip_code'],
            'phone': peer_df['phone'],
            'email': peer_df['email'],
            'website': '',
            'service_types': 'Peer Support',
            'hours': 'Varies by location',
            'populations_served': 'Adults, Families',
            'languages': 'English',
            'eligibility': 'Open to individuals in recovery and their loved ones',
            'payment_options': 'Free',
            'data_source': 'Peer Recovery Centers'
        })

        all_data.append(peer_standardized)
        print(f"Loaded {len(peer_standardized)} Peer Recovery centers")

    if not all_data:
        print("No data files found!")
        return None

    # Combine all datasets
    combined_df = pd.concat(all_data, ignore_index=True)

    # Remove duplicates based on name and address
    original_count = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=['name', 'address'], keep='first')
    duplicates_removed = original_count - len(combined_df)

    print(f"\nCombined dataset:")
    print(f"  Total records: {len(combined_df)}")
    print(f"  Duplicates removed: {duplicates_removed}")
    print(f"  Data sources: {combined_df['data_source'].value_counts().to_dict()}")
    print(f"  Cities covered: {combined_df['city'].nunique()}")

    # Save combined dataset
    output_file = DATA_DIR / "recovery_services.csv"
    combined_df.to_csv(output_file, index=False)
    print(f"\nSaved combined dataset to: {output_file}")

    return combined_df


if __name__ == '__main__':
    combine_datasets()
