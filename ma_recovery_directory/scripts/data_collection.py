#!/usr/bin/env python3
"""
Main data collection script for Massachusetts Recovery Services Directory
"""

import argparse
import logging
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from data_collection.scrapers.helpline_ma_scraper import HelplineMAScraper
from data_collection.scrapers.bsas_scraper import BSASLicensingScraper
from data_collection.scrapers.samhsa_scraper import SAMHSATreatmentLocatorScraper
from data_collection.processors.data_processor import RecoveryServicesDataProcessor
from config.settings import DATABASE_CONFIG, LOGGING_CONFIG, DATA_DIR

# Configure logging
logging.basicConfig(**LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class DataCollectionManager:
    def __init__(self):
        self.processor = RecoveryServicesDataProcessor()
        self.scrapers = {
            'helpline_ma': HelplineMAScraper(),
            'bsas': BSASLicensingScraper(),
            'samhsa': SAMHSATreatmentLocatorScraper()
        }
    
    def collect_all_data(self):
        """Collect data from all sources"""
        logger.info("Starting data collection from all sources")
        all_data = []
        
        for source_name, scraper in self.scrapers.items():
            try:
                logger.info(f"Collecting data from {source_name}")
                
                if source_name == 'helpline_ma':
                    raw_data = scraper.scrape_providers()
                elif source_name == 'bsas':
                    raw_data = scraper.scrape_licensed_providers()
                elif source_name == 'samhsa':
                    raw_data = scraper.search_massachusetts_providers()
                
                # Normalize data
                normalized_df = self.processor.normalize_data(raw_data, source_name)
                all_data.append(normalized_df)
                
                logger.info(f"Collected {len(normalized_df)} records from {source_name}")
                
            except Exception as e:
                logger.error(f"Error collecting data from {source_name}: {str(e)}")
                continue
        
        if not all_data:
            logger.error("No data collected from any source")
            return None
        
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        logger.info(f"Combined dataset contains {len(combined_df)} total records")
        
        # Process and clean data
        processed_df = self.process_combined_data(combined_df)
        
        return processed_df
    
    def process_combined_data(self, df):
        """Process and clean combined data"""
        logger.info("Processing combined data")
        
        # Deduplicate
        original_count = len(df)
        df = self.processor.deduplicate_providers(df)
        logger.info(f"Removed {original_count - len(df)} duplicate records")
        
        # Validate
        df = self.processor.validate_data(df)
        logger.info(f"Final dataset contains {len(df)} valid records")
        
        return df
    
    def save_data(self, df, filename=None):
        """Save processed data to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recovery_services_{timestamp}.csv"
        
        file_path = DATA_DIR / filename
        df.to_csv(file_path, index=False)
        logger.info(f"Data saved to {file_path}")
        
        # Also save as the main dataset
        main_file = DATABASE_CONFIG['file_path']
        df.to_csv(main_file, index=False)
        logger.info(f"Main dataset updated at {main_file}")
        
        return file_path
    
    def collect_from_source(self, source_name):
        """Collect data from a specific source"""
        if source_name not in self.scrapers:
            logger.error(f"Unknown source: {source_name}")
            return None
        
        logger.info(f"Collecting data from {source_name}")
        scraper = self.scrapers[source_name]
        
        try:
            if source_name == 'helpline_ma':
                raw_data = scraper.scrape_providers()
            elif source_name == 'bsas':
                raw_data = scraper.scrape_licensed_providers()
            elif source_name == 'samhsa':
                raw_data = scraper.search_massachusetts_providers()
            
            # Normalize data
            normalized_df = self.processor.normalize_data(raw_data, source_name)
            
            # Validate
            validated_df = self.processor.validate_data(normalized_df)
            
            logger.info(f"Collected {len(validated_df)} valid records from {source_name}")
            
            return validated_df
            
        except Exception as e:
            logger.error(f"Error collecting data from {source_name}: {str(e)}")
            return None


def main():
    parser = argparse.ArgumentParser(description='Collect Massachusetts recovery services data')
    parser.add_argument('--source', choices=['helpline_ma', 'bsas', 'samhsa', 'all'], 
                       default='all', help='Data source to collect from')
    parser.add_argument('--output', help='Output filename (optional)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Run without saving data')
    
    args = parser.parse_args()
    
    manager = DataCollectionManager()
    
    if args.source == 'all':
        df = manager.collect_all_data()
    else:
        df = manager.collect_from_source(args.source)
    
    if df is None:
        logger.error("No data collected")
        sys.exit(1)
    
    if not args.dry_run:
        output_file = manager.save_data(df, args.output)
        print(f"Data collection complete. Output saved to: {output_file}")
    else:
        print(f"Dry run complete. Would have saved {len(df)} records.")
    
    # Print summary
    print(f"\nSummary:")
    print(f"Total records: {len(df)}")
    print(f"Data sources: {df['data_source'].value_counts().to_dict()}")
    print(f"Cities covered: {df['city'].nunique()}")
    print(f"Service types: {df['service_types'].str.split(',').explode().nunique()}")


if __name__ == '__main__':
    main()