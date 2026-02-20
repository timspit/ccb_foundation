"""
Scraper for BSAS licensing database (Mass.gov)
"""

import requests
import pandas as pd
import time
import re
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BSASLicensingScraper:
    def __init__(self, delay: float = 1.0, max_retries: int = 3):
        """
        Initialize BSAS scraper
        
        Args:
            delay: Delay between requests in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.base_url = "https://hhsvgapps03.hhs.state.ma.us"
        self.main_url = f"{self.base_url}/elicensing-pubweb/prog/main.htm"
        self.delay = delay
        self.max_retries = max_retries
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Setup headers to appear more like a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def scrape_licensed_providers(self) -> List[Dict]:
        """
        Scrape all licensed provider data from BSAS database
        
        Returns:
            List of provider dictionaries with extracted data
        """
        providers = []
        
        try:
            # Get the main page to understand the structure
            self.logger.info("Fetching main BSAS licensing page")
            response = self._make_request(self.main_url)
            if not response:
                return providers
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for city/location links or direct provider listings
            city_links = self._extract_city_links(soup)
            
            if city_links:
                # If there are city links, scrape each city
                for city_name, city_url in city_links:
                    self.logger.info(f"Scraping providers for {city_name}")
                    city_providers = self._scrape_city_providers(city_url)
                    providers.extend(city_providers)
                    time.sleep(self.delay)  # Rate limiting
            else:
                # If no city links, try to extract providers directly from main page
                self.logger.info("Extracting providers from main page")
                providers = self._extract_providers_from_page(soup)
                
        except Exception as e:
            self.logger.error(f"Error scraping BSAS providers: {str(e)}")
            
        self.logger.info(f"Successfully scraped {len(providers)} providers from BSAS")
        return providers
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Make HTTP request with error handling"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {str(e)}")
            return None
    
    def _extract_city_links(self, soup: BeautifulSoup) -> List[tuple]:
        """Extract city/location links from main page"""
        city_links = []
        
        # Look for links that contain cityId parameter (specific to BSAS structure)
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Filter for city links with cityId parameter
            if href and 'cityId=' in href:
                full_url = urljoin(self.base_url, href)
                city_links.append((text, full_url))
        
        return city_links
    
    def _scrape_city_providers(self, city_url: str) -> List[Dict]:
        """Scrape providers from a specific city page"""
        providers = []
        
        response = self._make_request(city_url)
        if not response:
            return providers
            
        soup = BeautifulSoup(response.content, 'html.parser')
        providers = self._extract_providers_from_page(soup)
        
        return providers
    
    def _extract_providers_from_page(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract provider information from a page"""
        providers = []
        
        # Get the raw text and parse it manually since BSAS uses a specific text format
        page_text = soup.get_text()
        
        # Look for the section with provider listings
        # Usually starts with "Substance Addiction Treatment Programs in [City]:"
        lines = page_text.split('\n')
        current_provider = {}
        in_provider_section = False
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if we're in a provider section
            if 'Substance Addiction Treatment Programs' in line:
                in_provider_section = True
                i += 1
                continue
                
            if not in_provider_section:
                i += 1
                continue
            
            if not line:
                i += 1
                continue
            
            # Parse provider fields based on BSAS format
            # The pattern is: field label on one line, value on the next line
            if line == 'Program name:':
                # Start of new provider - save previous if exists
                if current_provider and current_provider.get('name'):
                    providers.append(current_provider)
                current_provider = self._create_empty_provider_dict()
                
                # Get the actual name from next line
                if i + 1 < len(lines):
                    current_provider['name'] = lines[i + 1].strip()
                i += 2  # Skip both lines
                continue
                
            elif line == 'Organization name:':
                if i + 1 < len(lines):
                    current_provider['organization'] = lines[i + 1].strip()
                i += 2
                continue
                
            elif line == 'Site Type:':
                if i + 1 < len(lines):
                    current_provider['site_type'] = lines[i + 1].strip()
                i += 2
                continue
                
            elif line == 'Service Setting:':
                if i + 1 < len(lines):
                    current_provider['service_setting'] = lines[i + 1].strip()
                i += 2
                continue
                
            elif line == 'Address:':
                if i + 1 < len(lines):
                    address = lines[i + 1].strip()
                    current_provider['address'] = address
                    # Try to extract city and zip from address
                    self._parse_address(address, current_provider)
                i += 2
                continue
                
            elif line == 'Phone:':
                if i + 1 < len(lines):
                    current_provider['phone'] = lines[i + 1].strip()
                i += 2
                continue
                
            elif line == 'Website:':
                if i + 1 < len(lines):
                    website = lines[i + 1].strip()
                    if website and website != 'None' and website.lower() != 'none':
                        current_provider['website'] = website
                i += 2
                continue
                    
            elif line == 'Licensed:':
                if i + 1 < len(lines):
                    license_status = lines[i + 1].strip()
                    current_provider['status'] = 'Active' if license_status.lower() == 'yes' else 'Inactive'
                i += 2
                continue
                
            elif line == 'Contracted:':
                if i + 1 < len(lines):
                    current_provider['contracted'] = lines[i + 1].strip()
                i += 2
                continue
                
            i += 1
        
        # Don't forget the last provider
        if current_provider and current_provider.get('name'):
            providers.append(current_provider)
        
        return providers
    
    def _extract_provider_details(self, element) -> Dict:
        """Extract provider details from an HTML element"""
        details = {
            'source': 'BSAS',
            'name': '',
            'organization': '',
            'license_number': '',
            'license_type': '',
            'status': 'Active',  # Assume active unless stated otherwise
            'site_type': '',
            'service_setting': '',
            'address': '',
            'city': '',
            'state': 'MA',
            'zip_code': '',
            'phone': '',
            'website': '',
            'services_authorized': [],
            'scraped_at': pd.Timestamp.now().isoformat()
        }
        
        text = element.get_text(strip=True) if element else ''
        if not text or len(text) < 10:  # Skip if too short
            return {}
        
        # Extract name (usually the first line or in a header)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            details['name'] = lines[0]
        
        # Look for patterns in the text
        # Phone number
        phone_match = re.search(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', text)
        if phone_match:
            details['phone'] = phone_match.group(1)
        
        # Website
        website_match = re.search(r'(https?://[^\s]+|www\.[^\s]+)', text, re.I)
        if website_match:
            details['website'] = website_match.group(1)
        
        # Address (look for patterns with street numbers and common street suffixes)
        address_match = re.search(r'\d+\s+[A-Za-z\s]+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)', text, re.I)
        if address_match:
            details['address'] = address_match.group(0)
        
        # ZIP code
        zip_match = re.search(r'\b\d{5}(-\d{4})?\b', text)
        if zip_match:
            details['zip_code'] = zip_match.group(0)
        
        # License number (look for patterns with "License" or numbers)
        license_match = re.search(r'License[#\s]*:?\s*([A-Z0-9-]+)', text, re.I)
        if license_match:
            details['license_number'] = license_match.group(1)
        
        # Look for service types or program types
        service_keywords = [
            'Outpatient', 'Inpatient', 'Residential', 'Detoxification', 'Methadone',
            'Suboxone', 'MAT', 'Medication Assisted Treatment', 'Counseling',
            'Group Therapy', 'Individual Therapy', 'IOP', 'Intensive Outpatient'
        ]
        
        found_services = []
        for keyword in service_keywords:
            if keyword.lower() in text.lower():
                found_services.append(keyword)
        
        details['services_authorized'] = found_services
        
        # Try to extract city from address or surrounding text
        ma_cities = ['Boston', 'Worcester', 'Springfield', 'Lowell', 'Cambridge', 
                    'New Bedford', 'Brockton', 'Quincy', 'Lynn', 'Fall River']
        for city in ma_cities:
            if city.lower() in text.lower():
                details['city'] = city
                break
        
        return details
    
    def _create_empty_provider_dict(self) -> Dict:
        """Create an empty provider dictionary with all fields"""
        return {
            'source': 'BSAS',
            'name': '',
            'organization': '',
            'license_number': '',
            'license_type': '',
            'status': 'Active',
            'site_type': '',
            'service_setting': '',
            'address': '',
            'city': '',
            'state': 'MA',
            'zip_code': '',
            'phone': '',
            'website': '',
            'services_authorized': [],
            'contracted': '',
            'scraped_at': pd.Timestamp.now().isoformat()
        }
    
    def _parse_address(self, address: str, provider_dict: Dict):
        """Parse address to extract city and ZIP code"""
        if not address:
            return
            
        # Try to extract ZIP code
        zip_match = re.search(r'\b(\d{5}(-\d{4})?)\b', address)
        if zip_match:
            provider_dict['zip_code'] = zip_match.group(1)
        
        # Try to extract city (usually before state and ZIP)
        # Look for pattern: City, MA ZIP
        city_match = re.search(r'([A-Za-z\s]+),\s*MA\s*\d{5}', address)
        if city_match:
            # Extract everything before the comma as the city
            full_match = city_match.group(0)
            city = full_match.split(',')[0].strip()
            # Remove street address part - take last few words as city
            city_parts = city.split()
            if len(city_parts) > 3:  # If too many words, take last 2-3 as city
                city = ' '.join(city_parts[-2:])
            provider_dict['city'] = city.title()
    
    def normalize_provider_data(self, providers: List[Dict]) -> pd.DataFrame:
        """
        Normalize and clean provider data
        
        Args:
            providers: List of provider dictionaries
            
        Returns:
            Cleaned pandas DataFrame
        """
        if not providers:
            return pd.DataFrame()
            
        df = pd.DataFrame(providers)
        
        # Remove duplicates based on name and address
        df = df.drop_duplicates(subset=['name', 'address'], keep='first')
        
        # Clean phone numbers
        if 'phone' in df.columns:
            df['phone'] = df['phone'].apply(self._clean_phone_number)
        
        # Clean websites
        if 'website' in df.columns:
            df['website'] = df['website'].apply(self._clean_website)
        
        # Standardize address format
        if 'address' in df.columns:
            df['address'] = df['address'].apply(self._clean_address)
        
        # Remove rows with no meaningful data
        df = df[df['name'].str.len() > 2]
        
        return df
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and standardize phone number format"""
        if not phone:
            return ''
        
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Format as (XXX) XXX-XXXX if 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        return phone  # Return original if can't parse
    
    def _clean_website(self, website: str) -> str:
        """Clean and standardize website URLs"""
        if not website:
            return ''
        
        website = website.strip().lower()
        if website.startswith('www.'):
            website = 'https://' + website
        elif not website.startswith('http'):
            website = 'https://' + website
            
        return website
    
    def _clean_address(self, address: str) -> str:
        """Clean and standardize address format"""
        if not address:
            return ''
        
        # Basic cleaning
        address = re.sub(r'\s+', ' ', address.strip())
        address = address.title()  # Title case
        
        return address
    
    def save_to_csv(self, providers: List[Dict], filename: str = 'bsas_providers.csv'):
        """Save provider data to CSV file"""
        df = self.normalize_provider_data(providers)
        df.to_csv(filename, index=False)
        self.logger.info(f"Saved {len(df)} providers to {filename}")
        
    def save_to_excel(self, providers: List[Dict], filename: str = 'bsas_providers.xlsx'):
        """Save provider data to Excel file"""
        df = self.normalize_provider_data(providers)
        df.to_excel(filename, index=False)
        self.logger.info(f"Saved {len(df)} providers to {filename}")