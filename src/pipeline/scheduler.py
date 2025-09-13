"""
Data pipeline scheduler for automated scraping.
"""

import schedule
import time
import logging
from datetime import datetime
from typing import List, Dict, Any
from src.scraper.google_maps_scraper import GoogleMapsScraper
from src.database.connection import DatabaseManager
from src.nlp.text_processor import TextProcessor
from src.utils.config import Config

logger = logging.getLogger(__name__)


class DataPipelineScheduler:
    """Scheduler for automated data pipeline execution."""
    
    def __init__(self, config: Config):
        self.config = config
        self.db_manager = DatabaseManager(config)
        self.text_processor = TextProcessor(config)
        self.scraper = None
        
        # Load scraping targets from config
        self.scraping_targets = self._load_scraping_targets()
    
    def _load_scraping_targets(self) -> List[Dict[str, Any]]:
        """Load scraping targets from configuration."""
        targets = self.config.get('pipeline.scraping_targets', [])
        
        if not targets:
            # Default targets if none configured
            targets = [
                {
                    'location': 'New York, NY',
                    'business_types': ['restaurants', 'hotels', 'shopping'],
                    'max_results': 50
                },
                {
                    'location': 'Los Angeles, CA',
                    'business_types': ['restaurants', 'hotels', 'shopping'],
                    'max_results': 50
                }
            ]
        
        return targets
    
    def run_scraping_job(self):
        """Run a single scraping job."""
        logger.info("Starting scheduled scraping job")
        
        try:
            with GoogleMapsScraper(self.config) as scraper:
                for target in self.scraping_targets:
                    location = target['location']
                    business_types = target['business_types']
                    max_results = target.get('max_results', 100)
                    
                    logger.info(f"Scraping {location} for business types: {business_types}")
                    
                    for business_type in business_types:
                        try:
                            # Scrape businesses
                            businesses = scraper.scrape_businesses(
                                location=location,
                                business_type=business_type,
                                max_results=max_results
                            )
                            
                            # Process and store data
                            self._process_and_store_businesses(businesses)
                            
                            logger.info(f"Scraped {len(businesses)} {business_type} businesses in {location}")
                            
                        except Exception as e:
                            logger.error(f"Error scraping {business_type} in {location}: {e}")
                            continue
                    
                    # Add delay between locations
                    time.sleep(self.config.get('scraping.delay_between_requests', 2))
            
            logger.info("Scheduled scraping job completed")
            
        except Exception as e:
            logger.error(f"Error in scheduled scraping job: {e}")
    
    def _process_and_store_businesses(self, businesses: List[Any]):
        """Process and store business data."""
        for business in businesses:
            try:
                # Store business information
                business_id = self.db_manager.store_business(business)
                
                # Process and store reviews
                if business.reviews:
                    processed_reviews = []
                    for review in business.reviews:
                        processed_review = self.text_processor.process_review(review)
                        processed_review['business_id'] = business_id
                        processed_reviews.append(processed_review)
                    
                    self.db_manager.store_reviews(processed_reviews)
                
                logger.debug(f"Stored business: {business.name}")
                
            except Exception as e:
                logger.error(f"Error processing business {business.name}: {e}")
                continue
    
    def start(self):
        """Start the scheduler."""
        frequency = self.config.get('pipeline.update_frequency', 'daily')
        
        if frequency == 'daily':
            schedule.every().day.at("02:00").do(self.run_scraping_job)
        elif frequency == 'weekly':
            schedule.every().monday.at("02:00").do(self.run_scraping_job)
        elif frequency == 'hourly':
            schedule.every().hour.do(self.run_scraping_job)
        else:
            logger.warning(f"Unknown frequency: {frequency}, defaulting to daily")
            schedule.every().day.at("02:00").do(self.run_scraping_job)
        
        logger.info(f"Scheduler started with {frequency} frequency")
        
        # Run initial job
        self.run_scraping_job()
        
        # Keep scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the scheduler."""
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def add_scraping_target(self, location: str, business_types: List[str], max_results: int = 100):
        """Add a new scraping target."""
        target = {
            'location': location,
            'business_types': business_types,
            'max_results': max_results
        }
        
        self.scraping_targets.append(target)
        logger.info(f"Added scraping target: {location} - {business_types}")
    
    def remove_scraping_target(self, location: str):
        """Remove a scraping target."""
        self.scraping_targets = [
            target for target in self.scraping_targets 
            if target['location'] != location
        ]
        logger.info(f"Removed scraping target: {location}")
    
    def get_scraping_targets(self) -> List[Dict[str, Any]]:
        """Get current scraping targets."""
        return self.scraping_targets.copy()
