"""
Configuration settings for Massachusetts Recovery Services Directory
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Data directories
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
EXPORTS_DIR = BASE_DIR / "exports"

# Ensure directories exist
for directory in [DATA_DIR, LOGS_DIR, EXPORTS_DIR]:
    directory.mkdir(exist_ok=True)

# Database settings
DATABASE_CONFIG = {
    'file_path': DATA_DIR / "recovery_services.csv",
    'backup_path': DATA_DIR / "backups",
    'schema_version': "1.0"
}

# Web application settings
FLASK_CONFIG = {
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-key-change-in-production'),
    'DEBUG': os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
    'HOST': os.environ.get('FLASK_HOST', '127.0.0.1'),
    'PORT': int(os.environ.get('FLASK_PORT', 5000))
}

# Data collection settings
SCRAPING_CONFIG = {
    'user_agent': 'MA-Recovery-Directory/1.0 (Contact: your-email@example.com)',
    'request_delay': 1,  # seconds between requests
    'max_retries': 3,
    'timeout': 30,
    'max_workers': 5  # for concurrent scraping
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'app.log',
            'formatter': 'default'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'console']
    }
}

# Export settings
EXPORT_CONFIG = {
    'formats': ['csv', 'excel', 'pdf'],
    'max_results': 1000,
    'temp_file_retention': 3600  # seconds
}

# Data validation rules
VALIDATION_RULES = {
    'phone_patterns': [
        r'^\(\d{3}\) \d{3}-\d{4}$',  # (123) 456-7890
        r'^\d{3}-\d{3}-\d{4}$',      # 123-456-7890
        r'^\d{10}$'                   # 1234567890
    ],
    'zip_code_pattern': r'^\d{5}(-\d{4})?$',
    'email_pattern': r'^[\w\.-]+@[\w\.-]+\.\w+$',
    'required_fields': ['name', 'phone'],
    'max_field_length': {
        'name': 200,
        'address': 300,
        'phone': 20,
        'email': 100,
        'website': 200
    }
}

# Service type mappings
SERVICE_TYPE_MAPPINGS = {
    'inpatient': ['Inpatient Treatment', 'Residential Treatment', 'Detox'],
    'outpatient': ['Outpatient Treatment', 'Intensive Outpatient', 'PHP'],
    'mat': ['Medication-Assisted Treatment', 'Methadone', 'Suboxone', 'Vivitrol'],
    'counseling': ['Individual Counseling', 'Group Therapy', 'Family Therapy'],
    'peer_support': ['Peer Support', 'Recovery Coaching', 'Support Groups'],
    'sober_living': ['Sober Living', 'Transitional Housing', 'Recovery Residence']
}

# Population mappings
POPULATION_MAPPINGS = {
    'adults': ['Adults', 'Men', 'Women'],
    'youth': ['Adolescents', 'Young Adults', 'Teenagers'],
    'special': ['LGBTQ+', 'Veterans', 'Pregnant Women', 'Parents with Children']
}

# Language mappings
LANGUAGE_MAPPINGS = {
    'english': 'English',
    'spanish': 'Spanish',
    'portuguese': 'Portuguese',
    'french': 'French',
    'haitian_creole': 'Haitian Creole',
    'chinese': 'Chinese',
    'vietnamese': 'Vietnamese'
}