# CCB Foundation - Massachusetts Recovery Services Directory

A centralized directory project for aggregating and normalizing addiction recovery services data across Massachusetts. This tool collects information from multiple official sources to create a comprehensive, searchable database of treatment providers.

## Project Overview

This repository contains tools to scrape, process, and manage data about substance use disorder treatment providers in Massachusetts. The system collects data from three primary sources:

1. **HelplineMA.org** - Massachusetts Substance Use Helpline
2. **BSAS Licensing Database** - Bureau of Substance Addiction Services (Mass.gov)
3. **SAMHSA Treatment Locator** - FindTreatment.gov federal database

## Virtual Environment Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone https://github.com/your-org/ccb_foundation.git
   cd ccb_foundation
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment**:

   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

   On Windows:
   ```bash
   venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   cd ma_recovery_directory
   pip install -r requirements.txt
   ```

5. **Verify installation**:
   ```bash
   python -c "import pandas; import requests; print('Setup successful!')"
   ```

### Deactivating the Virtual Environment

When you're done working, deactivate the virtual environment:
```bash
deactivate
```

## Current Implementation

### Project Structure

```
ma_recovery_directory/
├── data_collection/
│   ├── scrapers/
│   │   ├── helpline_ma_scraper.py    # HelplineMA.org scraper
│   │   ├── bsas_scraper.py           # BSAS licensing database scraper
│   │   └── samhsa_scraper.py         # SAMHSA treatment locator scraper
│   └── processors/
│       └── data_processor.py          # Data normalization and validation
├── config/
│   └── settings.py                    # Configuration and settings
├── scripts/
│   └── data_collection.py             # Main data collection orchestrator
├── requirements.txt                   # Python dependencies
└── setup.py                          # Package setup configuration
```

### Core Components

#### 1. Web Scrapers

**HelplineMA Scraper** (`helpline_ma_scraper.py`)
- Scrapes provider data from HelplineMA.org
- Extracts: name, address, phone, email, website, services, hours, populations served, languages, eligibility
- Status: Template structure ready for implementation

**BSAS Licensing Scraper** (`bsas_scraper.py`)
- Fully implemented scraper for Massachusetts Bureau of Substance Addiction Services database
- Features:
  - Robust retry strategy and rate limiting
  - Extracts licensed provider information including organization name, license status, service settings
  - Parses structured text data from government database
  - Data cleaning and normalization methods
  - Export to CSV and Excel formats
- Extracts: program name, organization, license info, site type, service setting, address, phone, website, license status

**SAMHSA Treatment Locator Scraper** (`samhsa_scraper.py`)
- Interfaces with FindTreatment.gov API
- Extracts: provider ID, name, address, phone, website, services, payment options, age groups, special programs, languages
- Status: Template structure ready for API implementation

#### 2. Data Processing Module (`data_processor.py`)

The `RecoveryServicesDataProcessor` class provides:

- **Data Normalization**: Converts data from different sources into a standardized format with fields:
  - Basic info: name, address, city, state, zip_code
  - Contact: phone, email, website
  - Services: service_types, hours, populations_served, languages
  - Other: eligibility, payment_options, data_source

- **Source-Specific Normalization**: Handles different data formats from HelplineMA, BSAS, and SAMHSA

- **Data Validation**:
  - Removes records missing critical information (name, phone)
  - Standardizes phone numbers to (XXX) XXX-XXXX format
  - Validates ZIP codes with regex pattern matching

- **Deduplication**: Removes duplicate providers based on name and address

#### 3. Configuration (`settings.py`)

Comprehensive configuration module including:

- **Directory Management**: Automatic creation of data, logs, and exports directories
- **Database Configuration**: CSV-based storage with backup paths
- **Flask Web Application Settings**: Host, port, debug mode (prepared for future web interface)
- **Scraping Configuration**: User agent, request delays, retry limits, concurrent workers
- **Logging Configuration**: File and console handlers with structured formatting
- **Export Settings**: Supports CSV, Excel, and PDF formats
- **Data Validation Rules**: Regex patterns for phone, ZIP codes, emails; required fields; max field lengths
- **Service Type Mappings**: Categorization of inpatient, outpatient, MAT, counseling, peer support, sober living
- **Population Mappings**: Adults, youth, special populations (LGBTQ+, veterans, pregnant women, etc.)
- **Language Mappings**: English, Spanish, Portuguese, French, Haitian Creole, Chinese, Vietnamese

#### 4. Data Collection Orchestrator (`data_collection.py`)

The `DataCollectionManager` class coordinates the entire data collection process:

- **Multi-Source Collection**: Collects data from all three scrapers (HelplineMA, BSAS, SAMHSA)
- **Data Pipeline**:
  1. Scrape raw data from each source
  2. Normalize data into standard format
  3. Combine data from all sources
  4. Deduplicate providers
  5. Validate and clean data
  6. Save to CSV with timestamp

- **Command-Line Interface**:
  - `--source`: Choose specific source or 'all' (default: all)
  - `--output`: Specify output filename (optional)
  - `--dry-run`: Test without saving data

- **Logging**: Comprehensive logging of collection process, errors, and summary statistics

- **Summary Statistics**: Reports total records, data sources, cities covered, and service types

### Dependencies

Key Python packages (see `requirements.txt` for complete list):

- **Web Framework**: Flask 2.3.3
- **Data Processing**: pandas 2.1.0, numpy 1.24.3
- **Web Scraping**: requests, beautifulsoup4, lxml, selenium
- **Data Validation**: pydantic, cerberus
- **Configuration**: PyYAML, python-dotenv
- **Export Formats**: openpyxl, reportlab
- **Utilities**: tqdm, schedule
- **Development**: pytest, black, flake8

## Usage

### Running Data Collection

Collect from all sources:
```bash
python ma_recovery_directory/scripts/data_collection.py
```

Collect from a specific source:
```bash
python ma_recovery_directory/scripts/data_collection.py --source bsas
```

Dry run (test without saving):
```bash
python ma_recovery_directory/scripts/data_collection.py --dry-run
```

### Installation as Package

Install the package in development mode:
```bash
cd ma_recovery_directory
pip install -e .
```

Then use the console command:
```bash
ma-recovery-collect --source all
```

## Development Status

- **BSAS Scraper**: Fully implemented and functional
- **Data Processor**: Complete with normalization, validation, and deduplication
- **Configuration**: Comprehensive settings ready for production
- **Data Collection Manager**: Full pipeline orchestration implemented
- **HelplineMA Scraper**: Template structure ready for implementation
- **SAMHSA Scraper**: Template structure ready for API integration

## Next Steps

1. Complete implementation of HelplineMA scraper
2. Implement SAMHSA API integration
3. Develop Flask web interface for searching/browsing data
4. Add database backend (SQLAlchemy) for more robust data storage
5. Implement scheduled automated data collection
6. Create data quality monitoring and reporting
7. Add export functionality for multiple formats

## Contributing

When contributing to this repository, please ensure:
1. Virtual environment is activated
2. Code follows existing style (use `black` for formatting)
3. Tests pass (use `pytest`)
4. Logging is used for debugging rather than print statements

## License

This project is developed by the CCB Foundation to support access to addiction recovery services in Massachusetts.