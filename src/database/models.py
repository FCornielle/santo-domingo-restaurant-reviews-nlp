"""
Database models for the business scraper.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Business(Base):
    """Business information model."""
    __tablename__ = 'businesses'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    phone = Column(String(50))
    website = Column(String(500))
    rating = Column(Float)
    review_count = Column(Integer)
    business_type = Column(String(100), nullable=False)
    location = Column(String(255), nullable=False)
    coordinates = Column(JSON)  # Store lat/lng as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviews = relationship("Review", back_populates="business")


class Review(Base):
    """Review information model."""
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    text = Column(Text, nullable=False)
    reviewer = Column(String(255))
    rating = Column(Integer)
    sentiment_score = Column(Float)
    sentiment_label = Column(String(50))
    processed_text = Column(Text)  # Cleaned/processed text
    keywords = Column(JSON)  # Extracted keywords
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    business = relationship("Business", back_populates="reviews")


class ScrapingSession(Base):
    """Scraping session tracking model."""
    __tablename__ = 'scraping_sessions'
    
    id = Column(Integer, primary_key=True)
    location = Column(String(255), nullable=False)
    business_type = Column(String(100), nullable=False)
    businesses_scraped = Column(Integer, default=0)
    reviews_scraped = Column(Integer, default=0)
    status = Column(String(50), default='running')  # running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)


class MarketAnalysis(Base):
    """Market analysis results model."""
    __tablename__ = 'market_analysis'
    
    id = Column(Integer, primary_key=True)
    location = Column(String(255), nullable=False)
    business_type = Column(String(100), nullable=False)
    analysis_type = Column(String(100), nullable=False)  # sentiment, keywords, trends
    results = Column(JSON)  # Analysis results as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
