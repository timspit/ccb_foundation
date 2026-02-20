#!/usr/bin/env python3
"""
Debug the parsing logic specifically
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from data_collection.scrapers.bsas_scraper import BSASLicensingScraper
from bs4 import BeautifulSoup

def main():
    scraper = BSASLicensingScraper()
    
    # Test with Boston
    boston_url = "https://hhsvgapps03.hhs.state.ma.us/elicensing-pubweb/prog/main.htm?initialLetter=B&cityId=36"
    
    response = scraper._make_request(boston_url)
    if response:
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        
        lines = text.split('\n')
        
        print("Looking for parsing patterns...")
        
        # Simulate the parsing logic with debug output
        current_provider = {}
        in_provider_section = False
        provider_count = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check for section header
            if 'Substance Addiction Treatment Programs' in line:
                print(f"Line {i}: Found section header: {line}")
                in_provider_section = True
                continue
                
            if not in_provider_section:
                continue
                
            if not line:
                if current_provider and current_provider.get('name'):
                    provider_count += 1
                    print(f"\nProvider {provider_count}: {current_provider.get('name', 'NO NAME')}")
                    current_provider = {}
                continue
            
            # Look for provider fields
            if line.startswith('Program name:'):
                if current_provider and current_provider.get('name'):
                    provider_count += 1
                    print(f"\nProvider {provider_count}: {current_provider.get('name', 'NO NAME')}")
                
                current_provider = scraper._create_empty_provider_dict()
                current_provider['name'] = line.replace('Program name:', '').strip()
                print(f"Line {i}: Found program name: {current_provider['name']}")
                
            elif line.startswith('Organization name:'):
                org = line.replace('Organization name:', '').strip()
                current_provider['organization'] = org
                print(f"Line {i}: Found organization: {org}")
                
            elif line.startswith('Address:'):
                addr = line.replace('Address:', '').strip()
                current_provider['address'] = addr
                print(f"Line {i}: Found address: {addr}")
                
            elif line.startswith('Phone:'):
                phone = line.replace('Phone:', '').strip()
                current_provider['phone'] = phone
                print(f"Line {i}: Found phone: {phone}")
        
        # Don't forget last provider
        if current_provider and current_provider.get('name'):
            provider_count += 1
            print(f"\nProvider {provider_count}: {current_provider.get('name', 'NO NAME')}")
            
        print(f"\nTotal providers found: {provider_count}")
    
if __name__ == "__main__":
    main()