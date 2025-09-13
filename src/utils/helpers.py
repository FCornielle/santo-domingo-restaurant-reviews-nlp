"""
Helper utilities for the business scraper.
"""

import logging
import time
import random
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Set up logging configuration."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler()]
    
    if log_file:
        # Create logs directory if it doesn't exist
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
    """Add random delay to avoid being detected as a bot."""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Retry function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)


def validate_location(location: str) -> bool:
    """Validate location string format."""
    if not location or not isinstance(location, str):
        return False
    
    # Basic validation - should contain at least one comma or be a single word
    return len(location.strip()) > 0 and (',' in location or len(location.split()) == 1)


def validate_business_type(business_type: str) -> bool:
    """Validate business type string."""
    if not business_type or not isinstance(business_type, str):
        return False
    
    # Basic validation - should be a single word or phrase
    return len(business_type.strip()) > 0 and len(business_type.split()) <= 3


def format_business_data(business: Any) -> Dict[str, Any]:
    """Format business data for storage."""
    return {
        'name': business.name,
        'address': business.address,
        'phone': business.phone,
        'website': business.website,
        'rating': business.rating,
        'review_count': business.review_count,
        'business_type': business.business_type,
        'location': business.location,
        'coordinates': business.coordinates,
        'reviews': business.reviews
    }


def save_data_to_json(data: List[Dict[str, Any]], filepath: str):
    """Save data to JSON file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"Data saved to {filepath}")


def load_data_from_json(filepath: str) -> List[Dict[str, Any]]:
    """Load data from JSON file."""
    filepath = Path(filepath)
    
    if not filepath.exists():
        logger.warning(f"File {filepath} does not exist")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def clean_filename(filename: str) -> str:
    """Clean filename for safe file system usage."""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove extra spaces and limit length
    filename = '_'.join(filename.split())
    return filename[:100]  # Limit to 100 characters


def get_timestamp() -> str:
    """Get current timestamp as string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    if not url:
        return False
    
    return url.startswith(('http://', 'https://'))


def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to maximum length."""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries."""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with nested key support."""
    keys = key.split('.')
    current = dictionary
    
    try:
        for k in keys:
            current = current[k]
        return current
    except (KeyError, TypeError):
        return default


def format_phone_number(phone: str) -> Optional[str]:
    """Format phone number to standard format."""
    if not phone:
        return None
    
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    
    return phone  # Return original if can't format


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in kilometers."""
    from math import radians, cos, sin, asin, sqrt
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r


def is_business_hours() -> bool:
    """Check if current time is within business hours (9 AM - 6 PM)."""
    current_hour = datetime.now().hour
    return 9 <= current_hour <= 18


def get_user_agents() -> List[str]:
    """Get list of user agents for rotation."""
    return [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]


def get_random_user_agent() -> str:
    """Get random user agent from the list."""
    return random.choice(get_user_agents())


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude coordinates."""
    return -90 <= lat <= 90 and -180 <= lon <= 180


def format_rating(rating: float) -> str:
    """Format rating to display format."""
    if rating is None:
        return "N/A"
    
    return f"{rating:.1f}/5.0"


def format_review_count(count: int) -> str:
    """Format review count to display format."""
    if count is None:
        return "0 reviews"
    
    if count < 1000:
        return f"{count} reviews"
    elif count < 1000000:
        return f"{count/1000:.1f}K reviews"
    else:
        return f"{count/1000000:.1f}M reviews"
