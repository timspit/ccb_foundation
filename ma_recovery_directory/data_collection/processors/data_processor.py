"""
Data processing and normalization for recovery services directory
"""

import pandas as pd
from typing import List, Dict, Optional
import re


class RecoveryServicesDataProcessor:
    def __init__(self):
        self.standard_fields = [
            'name', 'address', 'city', 'state', 'zip_code',
            'phone', 'email', 'website', 'service_types',
            'hours', 'populations_served', 'languages',
            'eligibility', 'payment_options', 'data_source'
        ]
    
    def normalize_data(self, raw_data: List[Dict], source: str) -> pd.DataFrame:
        """Normalize data from different sources into standard format"""
        normalized_data = []
        
        for record in raw_data:
            normalized_record = self._normalize_record(record, source)
            normalized_data.append(normalized_record)
        
        return pd.DataFrame(normalized_data)
    
    def _normalize_record(self, record: Dict, source: str) -> Dict:
        """Normalize a single record"""
        normalized = {field: '' for field in self.standard_fields}
        normalized['data_source'] = source
        
        # Source-specific normalization logic
        if source == 'helpline_ma':
            normalized.update(self._normalize_helpline_ma(record))
        elif source == 'bsas':
            normalized.update(self._normalize_bsas(record))
        elif source == 'samhsa':
            normalized.update(self._normalize_samhsa(record))
        
        return normalized
    
    def _normalize_helpline_ma(self, record: Dict) -> Dict:
        """Normalize HelplineMA data"""
        return {}
    
    def _normalize_bsas(self, record: Dict) -> Dict:
        """Normalize BSAS data"""
        return {}
    
    def _normalize_samhsa(self, record: Dict) -> Dict:
        """Normalize SAMHSA data"""
        return {}
    
    def deduplicate_providers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate providers based on name and address"""
        return df.drop_duplicates(subset=['name', 'address'], keep='first')
    
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean data"""
        # Remove records missing critical information
        df = df.dropna(subset=['name', 'phone'])
        
        # Standardize phone numbers
        df['phone'] = df['phone'].apply(self._standardize_phone)
        
        # Validate zip codes
        df = df[df['zip_code'].str.match(r'^\d{5}(-\d{4})?$', na=False)]
        
        return df
    
    def _standardize_phone(self, phone: str) -> str:
        """Standardize phone number format"""
        if pd.isna(phone):
            return ''
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', str(phone))
        
        # Format as (XXX) XXX-XXXX
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        return phone