"""
Scraper for BSAS Peer Recovery Support Centers (Mass.gov)

Source: https://www.mass.gov/info-details/peer-recovery-support-centers
Contact: questions.bsas@state.ma.us
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime
import time


logger = logging.getLogger(__name__)


class PeerRecoveryCentersScraper:
    """
    Scraper for Massachusetts Peer Recovery Support Centers directory
    Data source: Mass.gov BSAS
    """

    def __init__(self):
        self.base_url = "https://www.mass.gov"
        self.directory_url = "https://www.mass.gov/info-details/peer-recovery-support-centers"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MA-Recovery-Directory/1.0 (Contact: questions.bsas@state.ma.us)',
            'Accept': 'text/html,application/xhtml+xml'
        })
        self.request_delay = 2  # seconds between requests
        self.max_retries = 3

    def scrape_all_centers(self) -> List[Dict]:
        """
        Scrape all peer recovery support centers from Mass.gov
        Falls back to static data if web scraping fails

        Returns:
            List of center dictionaries
        """
        logger.info("Scraping Peer Recovery Support Centers from Mass.gov")

        try:
            response = self.session.get(self.directory_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            centers = self._parse_centers(soup)

            if centers:
                logger.info(f"Found {len(centers)} Peer Recovery Support Centers via web scraping")
                return centers
            else:
                logger.warning("Web scraping returned no results, falling back to static data")
                return self.get_static_data()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching peer recovery centers: {e}")
            logger.info("Falling back to static data")
            return self.get_static_data()

    def _parse_centers(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse centers from page HTML"""
        centers = []

        # Find all region sections
        regions = ['Western', 'Central', 'Northeast', 'Metro West', 'Boston', 'Southeast']

        for region in regions:
            region_centers = self._parse_region(soup, region)
            centers.extend(region_centers)

        return centers

    def _parse_region(self, soup: BeautifulSoup, region: str) -> List[Dict]:
        """Parse centers from a specific region"""
        centers = []

        # Try to find region heading
        region_heading = soup.find(string=re.compile(f'{region} Region', re.IGNORECASE))

        if not region_heading:
            logger.warning(f"Could not find {region} region section")
            return centers

        # Find the table or list following the region heading
        parent = region_heading.find_parent()
        if not parent:
            return centers

        # Look for table rows
        table = parent.find_next('table')
        if table:
            rows = table.find_all('tr')[1:]  # Skip header row

            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    center = self._parse_table_row(cols, region)
                    if center:
                        centers.append(center)

        return centers

    def _parse_table_row(self, cols: List, region: str) -> Optional[Dict]:
        """Parse center information from table row"""
        try:
            name = cols[0].get_text(strip=True)
            address_text = cols[1].get_text(strip=True)
            phone = cols[2].get_text(strip=True) if len(cols) > 2 else ''
            email = cols[3].get_text(strip=True) if len(cols) > 3 else ''

            # Parse address
            address, city, zip_code = self._parse_address(address_text)

            # Clean phone number
            phone = self._clean_phone(phone)

            return {
                'name': name,
                'center_name': name,
                'address': address,
                'city': city,
                'state': 'MA',
                'zip_code': zip_code,
                'phone': phone,
                'email': email,
                'website': '',
                'region': region,
                'service_types': ['Peer Support', 'Recovery Support'],
                'services_offered': 'Peer recovery support services, support groups, linkage and referral',
                'hours': 'Varies by location',
                'populations_served': ['Adults', 'Families'],
                'languages': ['English'],
                'eligibility': 'Open to individuals in recovery and their loved ones',
                'data_source': 'BSAS Peer Recovery Centers',
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error parsing table row: {e}")
            return None

    def _parse_address(self, address_text: str) -> tuple:
        """
        Parse address string into components

        Args:
            address_text: Full address string (e.g., "123 Main St, Boston, MA 02101")

        Returns:
            Tuple of (street_address, city, zip_code)
        """
        # Try to extract city and zip
        parts = [p.strip() for p in address_text.split(',')]

        if len(parts) >= 2:
            street = ', '.join(parts[:-1])
            last_part = parts[-1]

            # Extract zip code from last part
            zip_match = re.search(r'\b\d{5}(-\d{4})?\b', last_part)
            zip_code = zip_match.group() if zip_match else ''

            # Extract city (text before state/zip)
            city_match = re.search(r'^([A-Za-z\s]+)', last_part)
            city = city_match.group(1).strip() if city_match else ''

            return street, city, zip_code

        return address_text, '', ''

    def _clean_phone(self, phone: str) -> str:
        """Clean and format phone number"""
        # Extract digits
        digits = re.sub(r'\D', '', phone)

        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"

        return phone

    def get_center_by_name(self, name: str) -> Optional[Dict]:
        """
        Search for a specific center by name

        Args:
            name: Center name to search for

        Returns:
            Center dictionary or None
        """
        centers = self.scrape_all_centers()

        for center in centers:
            if name.lower() in center['name'].lower():
                return center

        return None

    def get_centers_by_region(self, region: str) -> List[Dict]:
        """
        Get all centers in a specific region

        Args:
            region: Region name (e.g., 'Western', 'Central', 'Boston')

        Returns:
            List of center dictionaries
        """
        centers = self.scrape_all_centers()
        return [c for c in centers if c['region'] == region]

    def save_to_csv(self, centers: List[Dict], filename: str):
        """Save centers to CSV file"""
        if not centers:
            logger.warning("No centers to save")
            return

        df = pd.DataFrame(centers)
        df.to_csv(filename, index=False)
        logger.info(f"Saved {len(centers)} peer recovery centers to {filename}")

    def get_static_data(self) -> List[Dict]:
        """
        Return static data of all 40 peer recovery centers
        This is a fallback if web scraping fails or for immediate use
        Data as of Feb 2026 from Mass.gov
        """
        return [
            # Western Region
            {'name': 'Have Hope Peer Recovery Center', 'address': '37 Main St Suite 201', 'city': 'North Adams', 'state': 'MA', 'zip_code': '01247', 'phone': '(413) 499-0412', 'email': 'Caitlin.McKinnon@briencenter.org', 'region': 'Western', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'The RECOVER Project', 'address': '68 Federal St', 'city': 'Greenfield', 'state': 'MA', 'zip_code': '01301', 'phone': '(413) 774-5489', 'email': 'agodfrey@wmtc.org', 'region': 'Western', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Hope for Holyoke', 'address': '100 Suffolk St', 'city': 'Holyoke', 'state': 'MA', 'zip_code': '01040', 'phone': '(413) 561-1020', 'email': 'rrodriguez2@gandaracenter.org', 'region': 'Western', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Valor Recovery Center', 'address': '383 Worthington St', 'city': 'Springfield', 'state': 'MA', 'zip_code': '01103', 'phone': '(413) 507-3635', 'email': 'mlopez3@gandaracenter.org', 'region': 'Western', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Living in Recovery', 'address': '75 North St', 'city': 'Pittsfield', 'state': 'MA', 'zip_code': '01201', 'phone': '(413) 570-8243', 'email': 'jmacdonald@servicenet.org', 'region': 'Western', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Northampton Recovery Center', 'address': '25 Armory St', 'city': 'Northampton', 'state': 'MA', 'zip_code': '01060', 'phone': '(413) 834-4127', 'email': 'jsullivan@wmtcinfo.org', 'region': 'Western', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'South County Recovery Center', 'address': '67 State Rd', 'city': 'Great Barrington', 'state': 'MA', 'zip_code': '01230', 'phone': '(413) 645-3564', 'email': 'gary@rural-recovery.org', 'region': 'Western', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},

            # Central Region
            {'name': 'Everyday Miracles', 'address': '25 Pleasant St', 'city': 'Worcester', 'state': 'MA', 'zip_code': '01609', 'phone': '(774) 670-4622', 'email': 'everydaymiracles@spectrumhealthsystems.org', 'region': 'Central', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'No One Walks Alone (NOWA)', 'address': '9 Spring St', 'city': 'Whitinsville', 'state': 'MA', 'zip_code': '01588', 'phone': '(508) 266-0210', 'email': 'clepore@advocates.org', 'region': 'Central', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': "Alyssa's Place", 'address': '297 Central St', 'city': 'Gardner', 'state': 'MA', 'zip_code': '01440', 'phone': '(978) 632-0934', 'email': 'bwagoner@gaamha.org', 'region': 'Central', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Leaders of Restoration', 'address': '437 Main St', 'city': 'Fitchburg', 'state': 'MA', 'zip_code': '01420', 'phone': '(978) 987-1258', 'email': 'kpowers@rrcifitchburg.com', 'region': 'Central', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Ripple Effect', 'address': '40 Spruce St', 'city': 'Leominster', 'state': 'MA', 'zip_code': '01453', 'phone': '(978) 384-7337', 'email': 'lhebert@gaamha.org', 'region': 'Central', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Bridge to Hope', 'address': '219 Everett St', 'city': 'Southbridge', 'state': 'MA', 'zip_code': '01550', 'phone': '(508) 981-4091', 'email': 'Carmen.ortiz@spectrumhealthsystems.org', 'region': 'Central', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},

            # Northeast Region
            {'name': 'CORE Peer Recovery & Resource Center', 'address': '11-17 Parker St', 'city': 'Gloucester', 'state': 'MA', 'zip_code': '01930', 'phone': '(351) 217-1424', 'email': 'mollyd@corerecovery.org', 'region': 'Northeast', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'New Beginnings Peer Recovery Center', 'address': '487 Essex St', 'city': 'Lawrence', 'state': 'MA', 'zip_code': '01840', 'phone': '(978) 655-3674', 'email': 'newbeginnings@spectrumhealthsystems.org', 'region': 'Northeast', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Recovery Café Lowell', 'address': '20 Williams St', 'city': 'Lowell', 'state': 'MA', 'zip_code': '01851', 'phone': '(978) 677-6087', 'email': 'jmellen@riverbendmv.org', 'region': 'Northeast', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'The Bridge Recovery Center', 'address': '239 Commercial St', 'city': 'Malden', 'state': 'MA', 'zip_code': '02148', 'phone': '(781) 480-4937', 'email': 'jlanneville@maldenovercomingaddiction.org', 'region': 'Northeast', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Recovery Exchange Peer Support Center', 'address': '35 Exchange St', 'city': 'Lynn', 'state': 'MA', 'zip_code': '01901', 'phone': '(617) 980-9784', 'email': 'Kim.Patterson@spectrumhealthsystems.org', 'region': 'Northeast', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Ray of Light Recovery Café', 'address': '222 Washington St', 'city': 'Haverhill', 'state': 'MA', 'zip_code': '01832', 'phone': '(978) 886-8961', 'email': 'lcarrasquillo@riverbendmv.org', 'region': 'Northeast', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},

            # Metro West Region
            {'name': 'The Recovery Connection', 'address': '31 Main St', 'city': 'Marlborough', 'state': 'MA', 'zip_code': '01752', 'phone': '(508) 485-0298', 'email': 'john.marhefka@spectrumhealthsystems.org', 'region': 'Metro West', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'A New Way Recovery Center', 'address': '85 Quincy Ave Suite B', 'city': 'Quincy', 'state': 'MA', 'zip_code': '02169', 'phone': '(617) 302-3287', 'email': 'ANewWayRC@baystatecs.org', 'region': 'Metro West', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Wey of Life Peer Recovery Center', 'address': '383 Bridge St', 'city': 'Weymouth', 'state': 'MA', 'zip_code': '02191', 'phone': '(781) 812-1392', 'email': 'kesson@southshorepeerrecovery.org', 'region': 'Metro West', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Turning Point Recovery Center', 'address': '32 Common St', 'city': 'Walpole', 'state': 'MA', 'zip_code': '02081', 'phone': '(508) 668-3960', 'email': 'cobrien@baystatecs.org', 'region': 'Metro West', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Anchored in Recovery', 'address': '19 Concord St Suite 1', 'city': 'Framingham', 'state': 'MA', 'zip_code': '01702', 'phone': '(508) 424-2520', 'email': 'bnicholson@smoc.org', 'region': 'Metro West', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},

            # Boston Region
            {'name': 'Devine Recovery Center', 'address': '70 Devine Way', 'city': 'South Boston', 'state': 'MA', 'zip_code': '02127', 'phone': '(857) 496-1384', 'email': 'davedecourcey@gavinfoundation.org', 'region': 'Boston', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'STEPRox Recovery Support Center', 'address': '153 Blue Hill Ave', 'city': 'Roxbury', 'state': 'MA', 'zip_code': '02119', 'phone': '(617) 442-7837', 'email': 'lleverett@northsuffolk.org', 'region': 'Boston', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Room to Grow Recovery Center', 'address': '39 Boylston St', 'city': 'Boston', 'state': 'MA', 'zip_code': '02116', 'phone': '(781) 656-5027', 'email': 'shonterwilliams@STFRANCISHOUSE.ORG', 'region': 'Boston', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Recovery on the Harbor', 'address': '983 Bennington St', 'city': 'East Boston', 'state': 'MA', 'zip_code': '02128', 'phone': '(617) 874-8046', 'email': 'ACohen@Northsuffolk.org', 'region': 'Boston', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Torchlight Peer Recovery Support Center', 'address': '2 Washington St', 'city': 'Dorchester', 'state': 'MA', 'zip_code': '02121', 'phone': '(617) 465-1299', 'email': 'lamont@torchlightrecovery.org', 'region': 'Boston', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'JP Peer Recovery Center', 'address': '120 South St', 'city': 'Jamaica Plain', 'state': 'MA', 'zip_code': '02130', 'phone': '(617) 865-8487', 'email': 'hdemelo@vpi.org', 'region': 'Boston', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},

            # Southeast Region
            {'name': 'Stairway to Recovery', 'address': '90 Main St', 'city': 'Brockton', 'state': 'MA', 'zip_code': '02301', 'phone': '(774) 257-5660', 'email': 'tbarreira@gandaracenter.org', 'region': 'Southeast', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'PIER Recovery Center of Cape Cod', 'address': '209 Main St', 'city': 'Hyannis', 'state': 'MA', 'zip_code': '02601', 'phone': '(508) 827-6150', 'email': 'amartin@gandaracenter.org', 'region': 'Southeast', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Peer2Peer Recovery Support Center', 'address': '182 North Main St', 'city': 'Fall River', 'state': 'MA', 'zip_code': '02720', 'phone': '(508) 567-5086', 'email': 'dbarnes@steppingstoneinc.org', 'region': 'Southeast', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Plymouth Recovery Support Center', 'address': '5 Main St Extension', 'city': 'Plymouth', 'state': 'MA', 'zip_code': '02360', 'phone': '(774) 225-0723', 'email': 'rjencks@gandaracenter.org', 'region': 'Southeast', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'R.I.S.E Recovery Support Center', 'address': '497 Belleville Rd', 'city': 'New Bedford', 'state': 'MA', 'zip_code': '02745', 'phone': '(774) 762-4076', 'email': 'DDaniels@paaca.org', 'region': 'Southeast', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'The Red House', 'address': '12 Beach Rd', 'city': 'Oak Bluffs', 'state': 'MA', 'zip_code': '02557', 'phone': '(508) 693-7900', 'email': 'rcropper@mvcommunityservices.org', 'region': 'Southeast', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Falmouth Peer Recovery Center', 'address': '769 East Falmouth Hwy', 'city': 'East Falmouth', 'state': 'MA', 'zip_code': '02536', 'phone': '(508) 996-8900', 'email': 'awilsey@gandaracenter.org', 'region': 'Southeast', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
            {'name': 'Taunton Peer Recovery Support Center', 'address': '1 Washington St', 'city': 'Taunton', 'state': 'MA', 'zip_code': '02780', 'phone': '(508) 206-9010', 'email': 'lreid@comcounseling.org', 'region': 'Southeast', 'service_types': ['Peer Support'], 'data_source': 'BSAS Peer Recovery Centers'},
        ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scraper = PeerRecoveryCentersScraper()

    # Try web scraping first, fall back to static data
    centers = scraper.scrape_all_centers()

    if not centers:
        logger.info("Web scraping failed, using static data...")
        centers = scraper.get_static_data()

    if centers:
        scraper.save_to_csv(centers, 'peer_recovery_centers.csv')
        print(f"\nSuccessfully collected {len(centers)} peer recovery centers")
        print("Data saved to peer_recovery_centers.csv")
    else:
        print("Failed to collect peer recovery center data")
