#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from data_collection.scrapers.bsas_scraper import BSASLicensingScraper
from bs4 import BeautifulSoup

def main():
    scraper = BSASLicensingScraper()
    
    boston_url = "https://hhsvgapps03.hhs.state.ma.us/elicensing-pubweb/prog/main.htm?initialLetter=B&cityId=36"
    
    response = scraper._make_request(boston_url)
    if response:
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        
        lines = text.split('\n')
        
        # Look at lines around the first "Program name:" occurrence
        for i, line in enumerate(lines):
            if 'Program name:' in line:
                print(f"Context around line {i}:")
                start = max(0, i-3)
                end = min(len(lines), i+7)
                for j in range(start, end):
                    marker = ">>>" if j == i else "   "
                    print(f"{marker} {j:3d}: '{lines[j]}'")
                print("-" * 50)
                break  # Just show the first one
    
if __name__ == "__main__":
    main()