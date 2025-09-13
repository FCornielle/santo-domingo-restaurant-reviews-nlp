"""
Tests for the scraper module.
"""

import pytest
from unittest.mock import Mock, patch
from src.scraper.google_maps_scraper import GoogleMapsScraper, BusinessInfo
from src.utils.config import Config


class TestGoogleMapsScraper:
    """Test cases for GoogleMapsScraper."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=Config)
        config.get.return_value = True
        return config
    
    @pytest.fixture
    def scraper(self, mock_config):
        """Create scraper instance with mocked driver."""
        with patch('src.scraper.google_maps_scraper.webdriver') as mock_webdriver:
            mock_driver = Mock()
            mock_webdriver.Chrome.return_value = mock_driver
            scraper = GoogleMapsScraper(mock_config)
            scraper.driver = mock_driver
            return scraper
    
    def test_business_info_creation(self):
        """Test BusinessInfo dataclass creation."""
        business = BusinessInfo(
            name="Test Restaurant",
            address="123 Test St",
            phone="555-1234",
            website="https://test.com",
            rating=4.5,
            review_count=100,
            business_type="restaurant",
            location="Test City",
            reviews=[],
            coordinates={"lat": 40.7128, "lng": -74.0060}
        )
        
        assert business.name == "Test Restaurant"
        assert business.rating == 4.5
        assert business.business_type == "restaurant"
    
    def test_clean_text(self, scraper):
        """Test text cleaning functionality."""
        # This would test the text cleaning method if it were public
        # For now, we'll test through the process_review method
        pass
    
    def test_scraper_initialization(self, mock_config):
        """Test scraper initialization."""
        with patch('src.scraper.google_maps_scraper.webdriver') as mock_webdriver:
            mock_driver = Mock()
            mock_webdriver.Chrome.return_value = mock_driver
            
            scraper = GoogleMapsScraper(mock_config)
            
            assert scraper.config == mock_config
            assert scraper.driver == mock_driver
    
    def test_scraper_context_manager(self, mock_config):
        """Test scraper as context manager."""
        with patch('src.scraper.google_maps_scraper.webdriver') as mock_webdriver:
            mock_driver = Mock()
            mock_webdriver.Chrome.return_value = mock_driver
            
            with GoogleMapsScraper(mock_config) as scraper:
                assert scraper.driver == mock_driver
            
            # Driver should be closed when exiting context
            mock_driver.quit.assert_called_once()


class TestBusinessInfo:
    """Test cases for BusinessInfo dataclass."""
    
    def test_business_info_required_fields(self):
        """Test that required fields are properly set."""
        business = BusinessInfo(
            name="Test Business",
            address="123 Test St",
            business_type="restaurant",
            location="Test City",
            reviews=[]
        )
        
        assert business.name == "Test Business"
        assert business.address == "123 Test St"
        assert business.business_type == "restaurant"
        assert business.location == "Test City"
        assert business.reviews == []
    
    def test_business_info_optional_fields(self):
        """Test that optional fields can be None."""
        business = BusinessInfo(
            name="Test Business",
            address="123 Test St",
            business_type="restaurant",
            location="Test City",
            reviews=[]
        )
        
        assert business.phone is None
        assert business.website is None
        assert business.rating is None
        assert business.review_count is None
        assert business.coordinates is None
