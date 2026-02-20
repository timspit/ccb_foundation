"""
Scraper for Massachusetts Substance Use Helpline (HelplineMA.org)

Website: https://helplinema.org
Contact: info@helplinema.org

Note: This website implements bot protection (403 errors).
For data access, consider:
1. Contacting HelplineMA directly for API access or data partnership
2. Using selenium with browser automation
3. Manual data collection with permission
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import time
import re
from typing import List, Dict, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class HelplineMAScraper:
    """
    Scraper for Massachusetts Substance Use Helpline directory

    WARNING: This site blocks automated requests (403 errors).
    Consider contacting info@helplinema.org for legitimate data access.
    """

    def __init__(self, use_selenium: bool = False):
        """
        Initialize HelplineMA scraper

        Args:
            use_selenium: Use Selenium for JavaScript rendering (helps with bot detection)
        """
        self.base_url = "https://helplinema.org"
        self.search_url = f"{self.base_url}/treatment-recovery/treatment/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://helplinema.org/',
            'Connection': 'keep-alive'
        })
        self.use_selenium = use_selenium
        self.request_delay = 3  # seconds between requests
        self.max_retries = 3

    def scrape_providers(self, retry_on_403: bool = False) -> List[Dict]:
        """
        Scrape provider data from HelplineMA.org

        Args:
            retry_on_403: Whether to retry when encountering 403 errors

        Returns:
            List of provider dictionaries
        """
        if self.use_selenium:
            return self._scrape_with_selenium()
        else:
            return self._scrape_with_requests(retry_on_403)

    def _scrape_with_requests(self, retry_on_403: bool) -> List[Dict]:
        """Scrape using requests library"""
        logger.info("Attempting to scrape HelplineMA.org")

        try:
            response = self.session.get(
                self.search_url,
                timeout=30,
                allow_redirects=True
            )

            if response.status_code == 403:
                logger.error("403 Forbidden - HelplineMA blocks automated requests")
                logger.info("To access this data:")
                logger.info("1. Contact info@helplinema.org for API access")
                logger.info("2. Use selenium mode: HelplineMAScraper(use_selenium=True)")
                logger.info("3. Consider manual data collection with permission")
                return []

            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            providers = self._parse_providers(soup)

            logger.info(f"Found {len(providers)} providers from HelplineMA")
            return providers

        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping HelplineMA: {e}")
            return []

    def _scrape_with_selenium(self) -> List[Dict]:
        """
        Scrape using Selenium for JavaScript rendering
        Requires: pip install selenium
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
        except ImportError:
            logger.error("Selenium not installed. Install with: pip install selenium")
            return []

        logger.info("Scraping HelplineMA using Selenium")

        try:
            # Set up Chrome in headless mode
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')

            driver = webdriver.Chrome(options=options)
            driver.get(self.search_url)

            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Get page source and parse
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            providers = self._parse_providers(soup)

            driver.quit()

            logger.info(f"Found {len(providers)} providers using Selenium")
            return providers

        except Exception as e:
            logger.error(f"Selenium scraping failed: {e}")
            return []

    def _parse_providers(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse providers from page HTML"""
        providers = []

        # Look for provider listings - adjust selectors based on actual site structure
        provider_elements = soup.find_all(['div', 'article'], class_=re.compile(r'provider|listing|result'))

        for element in provider_elements:
            provider = self._parse_provider_element(element)
            if provider and provider.get('name'):
                providers.append(provider)

        return providers

    def _parse_provider_element(self, element) -> Optional[Dict]:
        """Parse individual provider element"""
        try:
            # These selectors are placeholders - adjust based on actual HTML structure
            name = element.find(['h2', 'h3', 'h4']).get_text(strip=True) if element.find(['h2', 'h3', 'h4']) else ''

            # Try to find address
            address_elem = element.find(class_=re.compile(r'address|location'))
            address = address_elem.get_text(strip=True) if address_elem else ''

            # Try to find phone
            phone_elem = element.find(string=re.compile(r'\(\d{3}\)|\d{3}-\d{3}-\d{4}'))
            phone = phone_elem.strip() if phone_elem else ''

            # Try to find email
            email_elem = element.find('a', href=re.compile(r'mailto:'))
            email = email_elem['href'].replace('mailto:', '') if email_elem else ''

            # Try to find website
            website_elem = element.find('a', href=re.compile(r'http'))
            website = website_elem['href'] if website_elem else ''

            return {
                'name': name,
                'address': address,
                'city': '',
                'state': 'MA',
                'zip_code': '',
                'phone': self._clean_phone(phone),
                'email': email,
                'website': website,
                'services': [],
                'service_types': [],
                'hours': '',
                'populations_served': [],
                'languages': [],
                'eligibility': '',
                'data_source': 'HelplineMA',
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error parsing provider element: {e}")
            return None

    def extract_provider_details(self, provider_url: str) -> Optional[Dict]:
        """
        Extract detailed information for a specific provider

        Args:
            provider_url: URL to provider detail page

        Returns:
            Provider details dictionary
        """
        try:
            response = self.session.get(provider_url, timeout=30)

            if response.status_code == 403:
                logger.error("403 Forbidden on provider detail page")
                return None

            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            details = {
                'name': '',
                'address': '',
                'phone': '',
                'email': '',
                'website': '',
                'services': [],
                'hours': '',
                'populations_served': [],
                'languages': [],
                'eligibility': '',
                'data_source': 'HelplineMA',
                'last_updated': datetime.now().isoformat()
            }

            # Parse details from page
            # Adjust selectors based on actual site structure

            time.sleep(self.request_delay)
            return details

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching provider details: {e}")
            return None

    def _clean_phone(self, phone: str) -> str:
        """Clean and format phone number"""
        digits = re.sub(r'\D', '', phone)

        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"

        return phone

    def save_to_csv(self, providers: List[Dict], filename: str):
        """Save providers to CSV file"""
        if not providers:
            logger.warning("No providers to save")
            return

        df = pd.DataFrame(providers)
        df.to_csv(filename, index=False)
        logger.info(f"Saved {len(providers)} HelplineMA providers to {filename}")

    def get_manual_collection_guide(self) -> str:
        """Return guidance for manual data collection"""
        return """
HelplineMA Data Collection Guide
================================

Since HelplineMA.org blocks automated scraping, here are alternatives:

1. REQUEST API ACCESS
   - Email: info@helplinema.org
   - Request: API access or data partnership for CCB Foundation recovery directory
   - Mention: Non-profit use case for public good

2. USE SELENIUM MODE
   - Install: pip install selenium
   - Install ChromeDriver
   - Run: scraper = HelplineMAScraper(use_selenium=True)

3. MANUAL COLLECTION
   - Visit: https://helplinema.org/treatment-recovery/treatment/
   - Export search results if available
   - Contact helpline directly: 1-800-327-5050

4. ALTERNATIVE DATA SOURCES
   - Use SAMHSA data (includes many same providers)
   - Use BSAS licensing database
   - Cross-reference with insurance provider directories

For questions, contact HelplineMA: info@helplinema.org
"""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scraper = HelplineMAScraper()

    # Attempt to scrape
    providers = scraper.scrape_providers()

    if providers:
        scraper.save_to_csv(providers, 'helplinema_providers.csv')
        print(f"Successfully collected {len(providers)} providers")
    else:
        print("\nHelplineMA scraping blocked (403 Forbidden)")
        print(scraper.get_manual_collection_guide())