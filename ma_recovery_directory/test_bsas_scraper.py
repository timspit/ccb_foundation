#!/usr/bin/env python3
"""
Test script for BSAS scraper
"""

import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from data_collection.scrapers.bsas_scraper import BSASLicensingScraper

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing BSAS Licensing Scraper...")
    print("=" * 50)
    
    # Initialize scraper
    scraper = BSASLicensingScraper(delay=2.0, max_retries=3)
    
    try:
        # Test scraping just Boston first (correct cityId)
        boston_url = "https://hhsvgapps03.hhs.state.ma.us/elicensing-pubweb/prog/main.htm?initialLetter=B&cityId=36"
        print(f"Testing with Boston URL: {boston_url}")
        
        response = scraper._make_request(boston_url)
        if response:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            providers = scraper._extract_providers_from_page(soup)
            
            print(f"\nScraping completed!")
            print(f"Found {len(providers)} providers from Boston")
        
        if providers:
            print("\nSample provider data:")
            print("-" * 30)
            
            # Show first few providers
            for i, provider in enumerate(providers[:3]):
                print(f"\nProvider {i+1}:")
                for key, value in provider.items():
                    if value:  # Only show non-empty values
                        print(f"  {key}: {value}")
            
            # Save results
            print(f"\nSaving results...")
            scraper.save_to_csv(providers, 'test_bsas_results.csv')
            
            # Show normalized data stats
            df = scraper.normalize_provider_data(providers)
            print(f"\nNormalized data statistics:")
            print(f"  Total providers after cleaning: {len(df)}")
            print(f"  Providers with phone numbers: {df['phone'].notna().sum()}")
            print(f"  Providers with websites: {df['website'].notna().sum()}")
            print(f"  Providers with addresses: {df['address'].notna().sum()}")
            
        else:
            print("No providers found. This might indicate:")
            print("- The website structure has changed")
            print("- Network connectivity issues")
            print("- Need to adjust the parsing logic")
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()