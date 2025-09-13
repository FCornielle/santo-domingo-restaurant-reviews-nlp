"""
Google Maps scraper for local business information.
"""

import time
import logging
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import requests
from dataclasses import dataclass
from src.utils.config import Config

logger = logging.getLogger(__name__)


@dataclass
class BusinessInfo:
    """Data class for business information."""
    name: str
    address: str
    phone: Optional[str]
    website: Optional[str]
    rating: Optional[float]
    review_count: Optional[int]
    business_type: str
    location: str
    reviews: List[Dict[str, str]]
    coordinates: Optional[Dict[str, float]]


class GoogleMapsScraper:
    """Scraper for Google Maps business data."""
    
    def __init__(self, config: Config):
        self.config = config
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Set up Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        
        if self.config.get('selenium.headless', True):
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(self.config.get('selenium.wait_time', 10))
    
    def search_businesses(self, location: str, business_type: str, max_results: int = 100) -> List[BusinessInfo]:
        """
        Search for businesses on Google Maps.
        
        Args:
            location: City or province to search in
            business_type: Type of business to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of BusinessInfo objects
        """
        query = f"{business_type} in {location}"
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        
        logger.info(f"Searching for: {query}")
        
        try:
            self.driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Wait for search results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[role="main"]'))
            )
            
            businesses = []
            processed_count = 0
            
            while processed_count < max_results:
                # Get all business listings
                business_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, '[data-result-index]'
                )
                
                if not business_elements:
                    logger.warning("No business elements found")
                    break
                
                for element in business_elements[processed_count:]:
                    if processed_count >= max_results:
                        break
                    
                    try:
                        business_info = self._extract_business_info(element, business_type, location)
                        if business_info:
                            businesses.append(business_info)
                            processed_count += 1
                            logger.info(f"Extracted business {processed_count}: {business_info.name}")
                            
                    except Exception as e:
                        logger.error(f"Error extracting business info: {e}")
                        continue
                
                # Scroll to load more results
                self._scroll_to_load_more()
                time.sleep(2)
            
            return businesses
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
    
    def _extract_business_info(self, element, business_type: str, location: str) -> Optional[BusinessInfo]:
        """Extract business information from a single element."""
        try:
            # Click on the business to get detailed info
            element.click()
            time.sleep(2)
            
            # Extract basic info
            name = self._safe_extract_text(By.CSS_SELECTOR, 'h1[data-attrid="title"]')
            address = self._safe_extract_text(By.CSS_SELECTOR, '[data-item-id="address"]')
            phone = self._safe_extract_text(By.CSS_SELECTOR, '[data-item-id="phone"]')
            website = self._safe_extract_link(By.CSS_SELECTOR, '[data-item-id="authority"]')
            
            # Extract rating
            rating_element = self.driver.find_element(By.CSS_SELECTOR, '.fontDisplayLarge')
            rating = float(rating_element.text) if rating_element else None
            
            # Extract review count
            review_count_element = self.driver.find_element(By.CSS_SELECTOR, '.fontBodyMedium')
            review_count = int(review_count_element.text.split()[0].replace(',', '')) if review_count_element else None
            
            # Extract reviews
            reviews = self._extract_reviews()
            
            # Extract coordinates (if available)
            coordinates = self._extract_coordinates()
            
            return BusinessInfo(
                name=name or "Unknown",
                address=address or "Unknown",
                phone=phone,
                website=website,
                rating=rating,
                review_count=review_count,
                business_type=business_type,
                location=location,
                reviews=reviews,
                coordinates=coordinates
            )
            
        except Exception as e:
            logger.error(f"Error extracting business info: {e}")
            return None
    
    def _safe_extract_text(self, by, selector) -> Optional[str]:
        """Safely extract text from an element."""
        try:
            element = self.driver.find_element(by, selector)
            return element.text.strip() if element else None
        except NoSuchElementException:
            return None
    
    def _safe_extract_link(self, by, selector) -> Optional[str]:
        """Safely extract link from an element."""
        try:
            element = self.driver.find_element(by, selector)
            return element.get_attribute('href') if element else None
        except NoSuchElementException:
            return None
    
    def _extract_reviews(self) -> List[Dict[str, str]]:
        """Extract reviews from the business page."""
        reviews = []
        
        try:
            # Click on reviews section
            reviews_button = self.driver.find_element(By.CSS_SELECTOR, '[data-value="Reviews"]')
            reviews_button.click()
            time.sleep(2)
            
            # Extract review elements
            review_elements = self.driver.find_elements(By.CSS_SELECTOR, '.jftiEf')
            
            for review_element in review_elements[:10]:  # Limit to 10 reviews
                try:
                    # Extract review text
                    review_text = review_element.find_element(By.CSS_SELECTOR, '.wiI7pd').text
                    
                    # Extract reviewer name
                    reviewer_name = review_element.find_element(By.CSS_SELECTOR, '.d4r55').text
                    
                    # Extract rating
                    rating_stars = review_element.find_elements(By.CSS_SELECTOR, '.kvMYJc')
                    rating = len(rating_stars) if rating_stars else None
                    
                    reviews.append({
                        'text': review_text,
                        'reviewer': reviewer_name,
                        'rating': rating
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting review: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting reviews: {e}")
        
        return reviews
    
    def _extract_coordinates(self) -> Optional[Dict[str, float]]:
        """Extract coordinates from the current URL."""
        try:
            current_url = self.driver.current_url
            if '@' in current_url:
                coords_part = current_url.split('@')[1].split(',')[0:2]
                return {
                    'lat': float(coords_part[0]),
                    'lng': float(coords_part[1])
                }
        except Exception as e:
            logger.error(f"Error extracting coordinates: {e}")
        return None
    
    def _scroll_to_load_more(self):
        """Scroll to load more search results."""
        try:
            # Scroll down to load more results
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error scrolling: {e}")
    
    def scrape_businesses(self, location: str, business_type: str, max_results: int = 100) -> List[BusinessInfo]:
        """Main method to scrape businesses."""
        return self.search_businesses(location, business_type, max_results)
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
