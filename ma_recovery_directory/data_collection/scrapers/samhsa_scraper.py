"""
Scraper for SAMHSA Behavioral Health Treatment Locator (FindTreatment.gov)

API Documentation: https://findtreatment.gov/assets/FindTreatment-Developer-Guide.pdf
API Access Request: https://findtreatment.gov/api-request-form
Contact: FindTreatment@samhsa.hhs.gov

Note: This API requires approval before use.
"""

import requests
import json
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class SAMHSATreatmentLocatorScraper:
    """
    Scraper for SAMHSA FindTreatment.gov API
    Requires API access approval from SAMHSA
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SAMHSA scraper

        Args:
            api_key: API key from SAMHSA (required after approval)
        """
        self.base_url = "https://findtreatment.gov"
        self.api_url = f"{self.base_url}/locator/exportsAsJson/v2"
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MA-Recovery-Directory/1.0',
            'Accept': 'application/json'
        })

        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})

        self.request_delay = 1  # seconds between requests
        self.max_retries = 3

    def _make_request(self, params: Dict) -> Optional[Dict]:
        """Make API request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    self.api_url,
                    params=params,
                    timeout=30
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    logger.error("API access denied. Please request API access at: https://findtreatment.gov/api-request-form")
                    return None
                elif response.status_code == 429:
                    logger.warning("Rate limit exceeded. Waiting before retry...")
                    time.sleep(5 * (attempt + 1))
                    continue
                else:
                    logger.error(f"API request failed with status {response.status_code}: {response.text}")
                    return None

            except requests.exceptions.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                return None

        return None

    def search_massachusetts_providers(
        self,
        state_code: str = "MA",
        service_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict]:
        """
        Search for substance abuse treatment providers in Massachusetts

        Args:
            state_code: State abbreviation (default: MA)
            service_type: Filter by service type (e.g., 'SA' for substance abuse)
            page: Page number for pagination
            page_size: Number of results per page

        Returns:
            List of provider dictionaries
        """
        if not self.api_key:
            logger.warning("No API key provided. Please request access at: https://findtreatment.gov/api-request-form")
            logger.info("Returning empty results. API key required for actual data collection.")
            return []

        params = {
            'sAddr': state_code,
            'sType': service_type or 'SA',  # SA = Substance Abuse
            'page': page,
            'pageSize': page_size
        }

        logger.info(f"Searching SAMHSA providers in {state_code} (page {page})")

        data = self._make_request(params)

        if not data:
            return []

        providers = []
        records = data.get('records', [])

        for record in records:
            provider = self._parse_provider(record)
            if provider:
                providers.append(provider)

        logger.info(f"Found {len(providers)} providers from SAMHSA")

        # Rate limiting
        time.sleep(self.request_delay)

        return providers

    def search_all_massachusetts_providers(self) -> List[Dict]:
        """
        Get all substance abuse treatment providers in Massachusetts
        Uses pagination to retrieve all results
        """
        all_providers = []
        page = 1

        while True:
            providers = self.search_massachusetts_providers(page=page)

            if not providers:
                break

            all_providers.extend(providers)
            logger.info(f"Retrieved page {page}, total so far: {len(all_providers)}")

            # Check if we got a full page (more pages might exist)
            if len(providers) < 100:
                break

            page += 1

        logger.info(f"Total SAMHSA providers collected: {len(all_providers)}")
        return all_providers

    def get_provider_details(self, provider_id: str) -> Optional[Dict]:
        """
        Get detailed information for a specific provider

        Args:
            provider_id: SAMHSA provider ID

        Returns:
            Provider details dictionary or None
        """
        params = {'id': provider_id}
        data = self._make_request(params)

        if data and data.get('records'):
            return self._parse_provider(data['records'][0])

        return None

    def _parse_provider(self, record: Dict) -> Dict:
        """Parse provider record from API response"""
        try:
            return {
                'provider_id': record.get('id', ''),
                'name': record.get('name1', ''),
                'address': self._format_address(record),
                'city': record.get('city', ''),
                'state': record.get('state', ''),
                'zip_code': record.get('zip', ''),
                'phone': record.get('phone', ''),
                'website': record.get('website', ''),
                'email': record.get('email', ''),
                'services': self._parse_services(record),
                'service_types': self._parse_service_types(record),
                'payment_options': self._parse_payment_options(record),
                'age_groups': self._parse_age_groups(record),
                'special_programs': self._parse_special_programs(record),
                'languages': self._parse_languages(record),
                'populations_served': self._parse_populations(record),
                'hours': record.get('hours', ''),
                'data_source': 'SAMHSA',
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error parsing provider record: {e}")
            return {}

    def _format_address(self, record: Dict) -> str:
        """Format address from record fields"""
        address_parts = []
        if record.get('street1'):
            address_parts.append(record['street1'])
        if record.get('street2'):
            address_parts.append(record['street2'])
        return ', '.join(address_parts)

    def _parse_services(self, record: Dict) -> List[str]:
        """Parse services offered"""
        services = []

        # Common SAMHSA service fields
        service_fields = [
            'detox', 'outpatient', 'residential', 'intensive_outpatient',
            'medication_assisted_treatment', 'buprenorphine', 'methadone',
            'naltrexone', 'counseling', 'group_therapy', 'individual_therapy'
        ]

        for field in service_fields:
            if record.get(field) == 'Y' or record.get(field) == True:
                services.append(field.replace('_', ' ').title())

        return services

    def _parse_service_types(self, record: Dict) -> List[str]:
        """Parse service types"""
        types = []

        if record.get('type_facility'):
            types.append(record['type_facility'])

        return types

    def _parse_payment_options(self, record: Dict) -> List[str]:
        """Parse payment options"""
        payment = []

        payment_fields = {
            'private_insurance': 'Private Insurance',
            'medicare': 'Medicare',
            'medicaid': 'Medicaid',
            'cash': 'Cash or Self-Payment',
            'sliding_scale': 'Sliding Scale',
            'payment_assistance': 'Payment Assistance'
        }

        for field, label in payment_fields.items():
            if record.get(field) == 'Y' or record.get(field) == True:
                payment.append(label)

        return payment

    def _parse_age_groups(self, record: Dict) -> List[str]:
        """Parse age groups served"""
        ages = []

        if record.get('adolescents') == 'Y':
            ages.append('Adolescents')
        if record.get('adults') == 'Y':
            ages.append('Adults')
        if record.get('seniors') == 'Y':
            ages.append('Seniors')

        return ages

    def _parse_special_programs(self, record: Dict) -> List[str]:
        """Parse special programs"""
        programs = []

        special_fields = {
            'pregnant_women': 'Pregnant/Postpartum Women',
            'veterans': 'Veterans',
            'lgbtq': 'LGBTQ+',
            'criminal_justice': 'Criminal Justice',
            'dui': 'DUI/DWI',
            'hearing_impaired': 'Hearing Impaired'
        }

        for field, label in special_fields.items():
            if record.get(field) == 'Y' or record.get(field) == True:
                programs.append(label)

        return programs

    def _parse_languages(self, record: Dict) -> List[str]:
        """Parse languages offered"""
        languages = []

        if record.get('spanish') == 'Y':
            languages.append('Spanish')
        if record.get('languages'):
            # Parse additional languages if provided as string
            lang_str = record['languages']
            if isinstance(lang_str, str):
                languages.extend([l.strip() for l in lang_str.split(',') if l.strip()])

        if 'English' not in languages:
            languages.insert(0, 'English')

        return languages

    def _parse_populations(self, record: Dict) -> List[str]:
        """Parse populations served"""
        populations = []

        if record.get('women_only') == 'Y':
            populations.append('Women')
        if record.get('men_only') == 'Y':
            populations.append('Men')
        if record.get('adolescents') == 'Y':
            populations.append('Adolescents')
        if record.get('adults') == 'Y':
            populations.append('Adults')

        return populations

    def save_to_csv(self, providers: List[Dict], filename: str):
        """Save providers to CSV file"""
        import pandas as pd

        if not providers:
            logger.warning("No providers to save")
            return

        df = pd.DataFrame(providers)
        df.to_csv(filename, index=False)
        logger.info(f"Saved {len(providers)} SAMHSA providers to {filename}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize scraper (API key needed for actual use)
    scraper = SAMHSATreatmentLocatorScraper()

    # Search for providers
    providers = scraper.search_all_massachusetts_providers()

    if providers:
        scraper.save_to_csv(providers, 'samhsa_providers.csv')
    else:
        print("\nTo use this scraper, you need to:")
        print("1. Request API access at: https://findtreatment.gov/api-request-form")
        print("2. Provide your API key when initializing the scraper")
        print("3. Example: scraper = SAMHSATreatmentLocatorScraper(api_key='your_key_here')")