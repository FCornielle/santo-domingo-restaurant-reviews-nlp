"""
Tests for the NLP module.
"""

import pytest
from unittest.mock import Mock, patch
from src.nlp.text_processor import TextProcessor
from src.nlp.sentiment_analyzer import SentimentAnalyzer
from src.utils.config import Config


class TestTextProcessor:
    """Test cases for TextProcessor."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=Config)
        config.get.return_value = './data/nltk_data'
        return config
    
    @pytest.fixture
    def text_processor(self, mock_config):
        """Create text processor instance."""
        with patch('src.nlp.text_processor.nltk.download') as mock_download:
            with patch('src.nlp.text_processor.nltk.data.path', []):
                return TextProcessor(mock_config)
    
    def test_clean_text(self, text_processor):
        """Test text cleaning functionality."""
        # Test URL removal
        text_with_url = "Check out this website https://example.com for more info"
        cleaned = text_processor.clean_text(text_with_url)
        assert "https://example.com" not in cleaned
        
        # Test email removal
        text_with_email = "Contact us at test@example.com for support"
        cleaned = text_processor.clean_text(text_with_email)
        assert "test@example.com" not in cleaned
        
        # Test phone number removal
        text_with_phone = "Call us at (555) 123-4567 for assistance"
        cleaned = text_processor.clean_text(text_with_phone)
        assert "(555) 123-4567" not in cleaned
        
        # Test whitespace normalization
        text_with_spaces = "This   has    extra    spaces"
        cleaned = text_processor.clean_text(text_with_spaces)
        assert "  " not in cleaned
    
    def test_tokenize_text(self, text_processor):
        """Test text tokenization."""
        text = "This is a test sentence with some words"
        tokens = text_processor.tokenize_text(text)
        
        assert isinstance(tokens, list)
        assert "this" in tokens
        assert "is" not in tokens  # Should be removed as stop word
        assert "test" in tokens
        assert "sentence" in tokens
    
    def test_extract_keywords(self, text_processor):
        """Test keyword extraction."""
        text = "This restaurant has excellent food and great service. The food is delicious and the service is outstanding."
        keywords = text_processor.extract_keywords(text, max_keywords=5)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        # Should contain meaningful words
        assert any(word in keywords for word in ["food", "service", "restaurant"])
    
    def test_analyze_sentiment(self, text_processor):
        """Test sentiment analysis."""
        positive_text = "I love this restaurant! The food is amazing and the service is excellent."
        negative_text = "This place is terrible. Bad food and poor service."
        neutral_text = "The restaurant is okay. Nothing special."
        
        positive_sentiment = text_processor.analyze_sentiment(positive_text)
        negative_sentiment = text_processor.analyze_sentiment(negative_text)
        neutral_sentiment = text_processor.analyze_sentiment(neutral_text)
        
        assert positive_sentiment['sentiment_score'] > 0
        assert negative_sentiment['sentiment_score'] < 0
        assert abs(neutral_sentiment['sentiment_score']) < 0.1
        
        assert positive_sentiment['sentiment_label'] == 'positive'
        assert negative_sentiment['sentiment_label'] == 'negative'
        assert neutral_sentiment['sentiment_label'] == 'neutral'
    
    def test_process_review(self, text_processor):
        """Test review processing."""
        review = {
            'text': 'Great food and excellent service!',
            'reviewer': 'John Doe',
            'rating': 5
        }
        
        processed = text_processor.process_review(review)
        
        assert 'processed_text' in processed
        assert 'keywords' in processed
        assert 'sentiment_score' in processed
        assert 'sentiment_label' in processed
        assert processed['sentiment_label'] == 'positive'


class TestSentimentAnalyzer:
    """Test cases for SentimentAnalyzer."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=Config)
        config.get.return_value = './data/nltk_data'
        return config
    
    @pytest.fixture
    def sentiment_analyzer(self, mock_config):
        """Create sentiment analyzer instance."""
        with patch('src.nlp.sentiment_analyzer.TextProcessor') as mock_text_processor:
            mock_text_processor.return_value = Mock()
            return SentimentAnalyzer(mock_config)
    
    def test_analyze_review_sentiment(self, sentiment_analyzer):
        """Test review sentiment analysis."""
        review_text = "The food was excellent but the service was slow."
        result = sentiment_analyzer.analyze_review_sentiment(review_text)
        
        assert 'sentiment_score' in result
        assert 'sentiment_label' in result
        assert 'confidence' in result
        assert 'aspects' in result
        assert isinstance(result['aspects'], dict)
    
    def test_extract_aspects(self, sentiment_analyzer):
        """Test aspect extraction."""
        text = "The food was delicious and the service was friendly, but the ambiance was too loud."
        aspects = sentiment_analyzer._extract_aspects(text)
        
        assert 'food' in aspects
        assert 'service' in aspects
        assert 'ambiance' in aspects
        assert 'price' in aspects
        assert 'location' in aspects
        
        # Food and service should be positive
        assert aspects['food'] > 0
        assert aspects['service'] > 0
        # Ambiance should be negative
        assert aspects['ambiance'] < 0
    
    def test_calculate_confidence(self, sentiment_analyzer):
        """Test confidence calculation."""
        # Test with short text
        short_text = "Good"
        confidence_short = sentiment_analyzer._calculate_confidence(short_text, 0.5)
        
        # Test with long text
        long_text = "This is a very detailed review with many words that provides comprehensive feedback about the experience."
        confidence_long = sentiment_analyzer._calculate_confidence(long_text, 0.8)
        
        assert 0 <= confidence_short <= 1
        assert 0 <= confidence_long <= 1
        assert confidence_long > confidence_short  # Longer text should have higher confidence
    
    def test_analyze_business_sentiment_trends(self, sentiment_analyzer):
        """Test business sentiment trend analysis."""
        # Mock reviews with different sentiment scores
        reviews = [
            {'text': 'Great place!', 'created_at': '2023-01-01'},
            {'text': 'Good food', 'created_at': '2023-01-02'},
            {'text': 'Excellent service', 'created_at': '2023-01-03'},
            {'text': 'Amazing experience', 'created_at': '2023-01-04'},
            {'text': 'Outstanding quality', 'created_at': '2023-01-05'}
        ]
        
        # Mock the analyze_review_sentiment method
        sentiment_analyzer.analyze_review_sentiment = Mock(side_effect=[
            {'sentiment_score': 0.1},
            {'sentiment_score': 0.2},
            {'sentiment_score': 0.3},
            {'sentiment_score': 0.4},
            {'sentiment_score': 0.5}
        ])
        
        result = sentiment_analyzer.analyze_business_sentiment_trends(reviews)
        
        assert 'trend_analysis' in result
        assert 'sentiment_trend' in result
        assert 'confidence' in result
        assert result['trend_analysis'] == 'improving'  # Should be improving trend
