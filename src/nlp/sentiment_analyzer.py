"""
Advanced sentiment analysis for business reviews.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
from collections import Counter
import re
from src.nlp.text_processor import TextProcessor
from src.utils.config import Config

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Advanced sentiment analysis for business reviews."""
    
    def __init__(self, config: Config):
        self.config = config
        self.text_processor = TextProcessor(config)
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def analyze_review_sentiment(self, review_text: str) -> Dict[str, Any]:
        """Analyze sentiment of a single review."""
        if not review_text:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'aspects': {}
            }
        
        # Basic sentiment analysis
        sentiment = self.text_processor.analyze_sentiment(review_text)
        
        # Extract aspects (food, service, ambiance, etc.)
        aspects = self._extract_aspects(review_text)
        
        # Calculate confidence based on text length and sentiment strength
        confidence = self._calculate_confidence(review_text, sentiment['sentiment_score'])
        
        return {
            'sentiment_score': sentiment['sentiment_score'],
            'sentiment_label': sentiment['sentiment_label'],
            'confidence': confidence,
            'aspects': aspects,
            'polarity': sentiment['polarity'],
            'subjectivity': sentiment['subjectivity']
        }
    
    def _extract_aspects(self, text: str) -> Dict[str, float]:
        """Extract aspect-based sentiment from text."""
        aspects = {
            'food': 0.0,
            'service': 0.0,
            'ambiance': 0.0,
            'price': 0.0,
            'location': 0.0
        }
        
        # Define aspect keywords
        aspect_keywords = {
            'food': ['food', 'dish', 'meal', 'taste', 'flavor', 'delicious', 'tasty', 'menu', 'cuisine'],
            'service': ['service', 'staff', 'waiter', 'waitress', 'server', 'friendly', 'helpful', 'attentive'],
            'ambiance': ['atmosphere', 'ambiance', 'decor', 'music', 'noise', 'quiet', 'loud', 'cozy', 'romantic'],
            'price': ['price', 'cost', 'expensive', 'cheap', 'affordable', 'value', 'worth', 'budget'],
            'location': ['location', 'parking', 'convenient', 'accessible', 'nearby', 'downtown', 'area']
        }
        
        # Analyze each aspect
        for aspect, keywords in aspect_keywords.items():
            aspect_text = self._extract_aspect_text(text, keywords)
            if aspect_text:
                aspect_sentiment = self.text_processor.analyze_sentiment(aspect_text)
                aspects[aspect] = aspect_sentiment['sentiment_score']
        
        return aspects
    
    def _extract_aspect_text(self, text: str, keywords: List[str]) -> str:
        """Extract text related to a specific aspect."""
        sentences = text.split('.')
        aspect_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in keywords):
                aspect_sentences.append(sentence.strip())
        
        return '. '.join(aspect_sentences)
    
    def _calculate_confidence(self, text: str, sentiment_score: float) -> float:
        """Calculate confidence score for sentiment analysis."""
        # Base confidence on text length and sentiment strength
        text_length = len(text.split())
        sentiment_strength = abs(sentiment_score)
        
        # Normalize text length (0-1 scale)
        length_score = min(text_length / 50, 1.0)
        
        # Combine length and sentiment strength
        confidence = (length_score * 0.6) + (sentiment_strength * 0.4)
        
        return min(confidence, 1.0)
    
    def analyze_business_sentiment_trends(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment trends for a business over time."""
        if not reviews:
            return {
                'trend_analysis': 'insufficient_data',
                'sentiment_trend': 0.0,
                'confidence': 0.0
            }
        
        # Sort reviews by date if available
        sorted_reviews = sorted(reviews, key=lambda x: x.get('created_at', ''))
        
        # Analyze sentiment for each review
        sentiment_scores = []
        for review in sorted_reviews:
            sentiment = self.analyze_review_sentiment(review.get('text', ''))
            sentiment_scores.append(sentiment['sentiment_score'])
        
        if len(sentiment_scores) < 2:
            return {
                'trend_analysis': 'insufficient_data',
                'sentiment_trend': 0.0,
                'confidence': 0.0
            }
        
        # Calculate trend (simple linear regression)
        x = np.arange(len(sentiment_scores))
        y = np.array(sentiment_scores)
        
        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]
        
        # Determine trend direction
        if slope > 0.01:
            trend_analysis = 'improving'
        elif slope < -0.01:
            trend_analysis = 'declining'
        else:
            trend_analysis = 'stable'
        
        # Calculate confidence based on data points and variance
        variance = np.var(sentiment_scores)
        confidence = max(0, 1 - variance) * min(len(sentiment_scores) / 10, 1)
        
        return {
            'trend_analysis': trend_analysis,
            'sentiment_trend': slope,
            'confidence': confidence,
            'total_reviews': len(sentiment_scores)
        }
    
    def cluster_reviews(self, reviews: List[Dict[str, Any]], n_clusters: int = 3) -> Dict[str, Any]:
        """Cluster reviews based on sentiment and content."""
        if not reviews:
            return {
                'clusters': [],
                'cluster_labels': []
            }
        
        # Extract text and sentiment scores
        texts = [review.get('text', '') for review in reviews]
        sentiment_scores = []
        
        for review in reviews:
            if 'sentiment_score' in review:
                sentiment_scores.append(review['sentiment_score'])
            else:
                sentiment = self.analyze_review_sentiment(review.get('text', ''))
                sentiment_scores.append(sentiment['sentiment_score'])
        
        # Vectorize texts
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            
            # Combine TF-IDF features with sentiment scores
            sentiment_array = np.array(sentiment_scores).reshape(-1, 1)
            features = np.hstack([tfidf_matrix.toarray(), sentiment_array])
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(features)
            
            # Analyze clusters
            clusters = []
            for i in range(n_clusters):
                cluster_reviews = [reviews[j] for j in range(len(reviews)) if cluster_labels[j] == i]
                cluster_sentiment = np.mean([sentiment_scores[j] for j in range(len(reviews)) if cluster_labels[j] == i])
                
                clusters.append({
                    'cluster_id': i,
                    'size': len(cluster_reviews),
                    'average_sentiment': cluster_sentiment,
                    'reviews': cluster_reviews
                })
            
            return {
                'clusters': clusters,
                'cluster_labels': cluster_labels.tolist()
            }
            
        except Exception as e:
            logger.error(f"Error clustering reviews: {e}")
            return {
                'clusters': [],
                'cluster_labels': []
            }
    
    def extract_topics(self, reviews: List[Dict[str, Any]], n_topics: int = 5) -> List[Dict[str, Any]]:
        """Extract topics from reviews using LDA."""
        if not reviews:
            return []
        
        # Extract texts
        texts = [review.get('text', '') for review in reviews if review.get('text')]
        
        if not texts:
            return []
        
        try:
            # Vectorize texts
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            
            # Apply LDA
            lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
            lda.fit(tfidf_matrix)
            
            # Extract topics
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            topics = []
            
            for topic_idx, topic in enumerate(lda.components_):
                top_words_idx = topic.argsort()[-10:][::-1]
                top_words = [feature_names[i] for i in top_words_idx]
                topic_weight = topic[top_words_idx[0]]
                
                topics.append({
                    'topic_id': topic_idx,
                    'top_words': top_words,
                    'weight': topic_weight
                })
            
            return topics
            
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []
    
    def generate_sentiment_report(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive sentiment analysis report."""
        if not reviews:
            return {
                'summary': 'No reviews available',
                'recommendations': []
            }
        
        # Basic sentiment analysis
        sentiment_summary = self.text_processor.generate_text_summary(reviews)
        
        # Trend analysis
        trend_analysis = self.analyze_business_sentiment_trends(reviews)
        
        # Topic extraction
        topics = self.extract_topics(reviews)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(sentiment_summary, trend_analysis)
        
        return {
            'summary': sentiment_summary,
            'trend_analysis': trend_analysis,
            'topics': topics,
            'recommendations': recommendations,
            'total_reviews': len(reviews)
        }
    
    def _generate_recommendations(self, sentiment_summary: Dict[str, Any], trend_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on sentiment analysis."""
        recommendations = []
        
        avg_sentiment = sentiment_summary.get('average_sentiment', 0)
        sentiment_dist = sentiment_summary.get('sentiment_distribution', {})
        trend = trend_analysis.get('trend_analysis', 'stable')
        
        # Sentiment-based recommendations
        if avg_sentiment < -0.1:
            recommendations.append("Consider addressing negative feedback and improving customer experience")
        elif avg_sentiment > 0.1:
            recommendations.append("Maintain current positive practices and consider expanding successful features")
        
        # Trend-based recommendations
        if trend == 'declining':
            recommendations.append("Investigate recent changes that may have caused declining sentiment")
        elif trend == 'improving':
            recommendations.append("Continue current improvements and monitor progress")
        
        # Distribution-based recommendations
        negative_pct = sentiment_dist.get('negative', 0) / sum(sentiment_dist.values()) * 100 if sum(sentiment_dist.values()) > 0 else 0
        if negative_pct > 30:
            recommendations.append("High percentage of negative reviews - prioritize customer service improvements")
        
        return recommendations
