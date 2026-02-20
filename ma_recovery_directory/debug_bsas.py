#!/usr/bin/env python3
"""
Debug script to examine BSAS page structure
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from data_collection.scrapers.bsas_scraper import BSASLicensingScraper
from bs4 import BeautifulSoup

def main():
    scraper = BSASLicensingScraper()
    
    # Test with Boston (correct cityId)
    boston_url = "https://hhsvgapps03.hhs.state.ma.us/elicensing-pubweb/prog/main.htm?initialLetter=B&cityId=36"
    print(f"Fetching: {boston_url}")
    
    response = scraper._make_request(boston_url)
    if response:
        print(f"Response status: {response.status_code}")
        print(f"Content length: {len(response.content)}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        
        # Show first 2000 characters to understand structure
        print("\nFirst 2000 characters of page content:")
        print("=" * 50)
        print(text[:2000])
        print("=" * 50)
        
        # Look for specific keywords
        if 'Program name:' in text:
            print("\n✓ Found 'Program name:' - parsing should work")
        else:
            print("\n✗ No 'Program name:' found - need different parsing approach")
            
        if 'Substance Addiction Treatment Programs' in text:
            print("✓ Found program section header")
        else:
            print("✗ No program section header found")
            
        # Look for any structured data patterns
        lines = text.split('\n')
        potential_providers = []
        for i, line in enumerate(lines):
            if 'program' in line.lower() and ('name' in line.lower() or ':' in line):
                potential_providers.append((i, line.strip()))
                
        print(f"\nFound {len(potential_providers)} potential provider lines:")
        for i, (line_num, line) in enumerate(potential_providers[:5]):  # Show first 5
            print(f"  {line_num}: {line}")
            
    else:
        print("Failed to fetch page")

if __name__ == "__main__":
    main()