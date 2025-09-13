"""
Configuration management for the scraper.
"""

import os
import yaml
from typing import Any, Dict
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration manager for the scraper."""
    
    def __init__(self, config_file: str = "config/settings.yaml"):
        self.config_file = config_file
        self.config = self._load_config()
        self._load_env_vars()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            # Create default config if it doesn't exist
            self._create_default_config()
        
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def _create_default_config(self):
        """Create default configuration file."""
        default_config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'business_scraper',
                'user': 'postgres',
                'password': 'password'
            },
            'selenium': {
                'headless': True,
                'wait_time': 10,
                'chrome_options': [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            },
            'scraping': {
                'max_results_per_search': 100,
                'delay_between_requests': 2,
                'max_retries': 3,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'nlp': {
                'sentiment_model': 'vader',
                'nltk_data_path': './data/nltk_data',
                'max_review_length': 1000
            },
            'pipeline': {
                'update_frequency': 'daily',
                'batch_size': 50,
                'enable_scheduling': True
            },
            'logging': {
                'level': 'INFO',
                'file': './logs/scraper.log',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }
        
        # Create config directory if it doesn't exist
        Path('config').mkdir(exist_ok=True)
        
        with open(self.config_file, 'w') as file:
            yaml.dump(default_config, file, default_flow_style=False)
    
    def _load_env_vars(self):
        """Load environment variables and override config values."""
        env_mappings = {
            'DB_HOST': 'database.host',
            'DB_PORT': 'database.port',
            'DB_NAME': 'database.name',
            'DB_USER': 'database.user',
            'DB_PASSWORD': 'database.password',
            'GOOGLE_MAPS_API_KEY': 'google_maps.api_key',
            'SELENIUM_HEADLESS': 'selenium.headless',
            'SELENIUM_WAIT_TIME': 'selenium.wait_time',
            'MAX_RESULTS_PER_SEARCH': 'scraping.max_results_per_search',
            'DELAY_BETWEEN_REQUESTS': 'scraping.delay_between_requests',
            'MAX_RETRIES': 'scraping.max_retries',
            'LOG_LEVEL': 'logging.level',
            'LOG_FILE': 'logging.file',
            'UPDATE_FREQUENCY': 'pipeline.update_frequency',
            'BATCH_SIZE': 'pipeline.batch_size'
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_value(config_path, value)
    
    def _set_nested_value(self, path: str, value: Any):
        """Set a nested value in the config dictionary."""
        keys = path.split('.')
        current = self.config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert string values to appropriate types
        if value.isdigit():
            current[keys[-1]] = int(value)
        elif value.lower() in ('true', 'false'):
            current[keys[-1]] = value.lower() == 'true'
        else:
            current[keys[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key path."""
        keys = key.split('.')
        current = self.config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set a configuration value by key path."""
        self._set_nested_value(key, value)
    
    def save(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as file:
            yaml.dump(self.config, file, default_flow_style=False)
