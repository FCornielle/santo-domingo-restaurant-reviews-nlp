"""
Text processing and NLP utilities for business reviews.
"""

import re
import logging
from typing import List, Dict, Any, Optional
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import string
from collections import Counter
from src.utils.config import Config

logger = logging.getLogger(__name__)


class TextProcessor:
    """Text processor for business reviews and comments."""
    
    def __init__(self, config: Config):
        self.config = config
        self.lemmatizer = WordNetLemmatizer()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.stop_words = set(stopwords.words('english'))
        
        # Download required NLTK data
        self._download_nltk_data()
    
    def _download_nltk_data(self):
        """Download required NLTK data."""
        try:
            nltk_data_path = self.config.get('nlp.nltk_data_path', './data/nltk_data')
            
            # Set NLTK data path
            nltk.data.path.append(nltk_data_path)
            
            # Download required data
            nltk.download('punkt', download_dir=nltk_data_path, quiet=True)
            nltk.download('stopwords', download_dir=nltk_data_path, quiet=True)
            nltk.download('wordnet', download_dir=nltk_data_path, quiet=True)
            nltk.download('vader_lexicon', download_dir=nltk_data_path, quiet=True)
            nltk.download('averaged_perceptron_tagger', download_dir=nltk_data_path, quiet=True)
            
            logger.info("NLTK data downloaded successfully")
            
        except Exception as e:
            logger.error(f"Error downloading NLTK data: {e}")
    
    def clean_text(self, text: str) -> str:
        """Clean and preprocess text."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove phone numbers
        text = re.sub(r'\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation except for sentence endings
        text = re.sub(r'[^\w\s.!?]', '', text)
        
        # Remove extra spaces
        text = text.strip()
        
        return text
    
    def tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words."""
        if not text:
            return []
        
        # Clean text first
        cleaned_text = self.clean_text(text)
        
        # Tokenize
        tokens = word_tokenize(cleaned_text)
        
        # Remove stop words and short words
        tokens = [
            token for token in tokens 
            if token not in self.stop_words 
            and len(token) > 2 
            and token not in string.punctuation
        ]
        
        return tokens
    
    def lemmatize_tokens(self, tokens: List[str]) -> List[str]:
        """Lemmatize tokens."""
        return [self.lemmatizer.lemmatize(token) for token in tokens]
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text."""
        if not text:
            return []
        
        # Tokenize and lemmatize
        tokens = self.tokenize_text(text)
        lemmatized_tokens = self.lemmatize_tokens(tokens)
        
        # Count word frequencies
        word_freq = Counter(lemmatized_tokens)
        
        # Get most common words
        keywords = [word for word, freq in word_freq.most_common(max_keywords)]
        
        return keywords
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text."""
        if not text:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'polarity': 0.0,
                'subjectivity': 0.0
            }
        
        # VADER sentiment analysis
        vader_scores = self.sentiment_analyzer.polarity_scores(text)
        
        # TextBlob sentiment analysis
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Determine sentiment label
        compound_score = vader_scores['compound']
        
        if compound_score >= 0.05:
            sentiment_label = 'positive'
        elif compound_score <= -0.05:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        return {
            'sentiment_score': compound_score,
            'sentiment_label': sentiment_label,
            'polarity': polarity,
            'subjectivity': subjectivity,
            'vader_scores': vader_scores
        }
    
    def process_review(self, review: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single review."""
        text = review.get('text', '')
        
        if not text:
            return review
        
        # Clean text
        cleaned_text = self.clean_text(text)
        
        # Tokenize
        tokens = self.tokenize_text(text)
        
        # Extract keywords
        keywords = self.extract_keywords(text)
        
        # Analyze sentiment
        sentiment = self.analyze_sentiment(text)
        
        # Add processed data to review
        processed_review = review.copy()
        processed_review.update({
            'processed_text': cleaned_text,
            'tokens': tokens,
            'keywords': keywords,
            'sentiment_score': sentiment['sentiment_score'],
            'sentiment_label': sentiment['sentiment_label'],
            'polarity': sentiment['polarity'],
            'subjectivity': sentiment['subjectivity']
        })
        
        return processed_review
    
    def process_business_reviews(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple reviews for a business."""
        processed_reviews = []
        
        for review in reviews:
            try:
                processed_review = self.process_review(review)
                processed_reviews.append(processed_review)
            except Exception as e:
                logger.error(f"Error processing review: {e}")
                continue
        
        return processed_reviews
    
    def analyze_business_sentiment(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall sentiment for a business."""
        if not reviews:
            return {
                'average_sentiment': 0.0,
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                'total_reviews': 0
            }
        
        sentiment_scores = []
        sentiment_labels = []
        
        for review in reviews:
            if 'sentiment_score' in review:
                sentiment_scores.append(review['sentiment_score'])
                sentiment_labels.append(review['sentiment_label'])
        
        if not sentiment_scores:
            return {
                'average_sentiment': 0.0,
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                'total_reviews': 0
            }
        
        # Calculate average sentiment
        average_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        
        # Count sentiment distribution
        sentiment_distribution = Counter(sentiment_labels)
        
        return {
            'average_sentiment': average_sentiment,
            'sentiment_distribution': dict(sentiment_distribution),
            'total_reviews': len(sentiment_scores)
        }
    
    def extract_common_keywords(self, reviews: List[Dict[str, Any]], top_n: int = 20) -> List[Dict[str, Any]]:
        """Extract common keywords across all reviews."""
        all_keywords = []
        
        for review in reviews:
            if 'keywords' in review:
                all_keywords.extend(review['keywords'])
        
        # Count keyword frequencies
        keyword_freq = Counter(all_keywords)
        
        # Get top keywords
        top_keywords = [
            {'keyword': keyword, 'frequency': freq}
            for keyword, freq in keyword_freq.most_common(top_n)
        ]
        
        return top_keywords
    
    def generate_text_summary(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of text analysis for a business."""
        if not reviews:
            return {
                'total_reviews': 0,
                'average_sentiment': 0.0,
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                'top_keywords': [],
                'average_rating': 0.0
            }
        
        # Process reviews if not already processed
        processed_reviews = []
        for review in reviews:
            if 'sentiment_score' not in review:
                processed_review = self.process_review(review)
                processed_reviews.append(processed_review)
            else:
                processed_reviews.append(review)
        
        # Analyze sentiment
        sentiment_analysis = self.analyze_business_sentiment(processed_reviews)
        
        # Extract common keywords
        top_keywords = self.extract_common_keywords(processed_reviews)
        
        # Calculate average rating
        ratings = [review.get('rating', 0) for review in processed_reviews if review.get('rating')]
        average_rating = sum(ratings) / len(ratings) if ratings else 0.0
        
        return {
            'total_reviews': len(processed_reviews),
            'average_sentiment': sentiment_analysis['average_sentiment'],
            'sentiment_distribution': sentiment_analysis['sentiment_distribution'],
            'top_keywords': top_keywords,
            'average_rating': average_rating
        }
