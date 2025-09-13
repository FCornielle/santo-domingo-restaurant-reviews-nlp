"""
Database connection and management.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from src.database.models import Base, Business, Review, ScrapingSession, MarketAnalysis
from src.utils.config import Config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for the scraper."""
    
    def __init__(self, config: Config):
        self.config = config
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._create_tables()
    
    def _create_engine(self):
        """Create database engine."""
        db_config = self.config.get('database', {})
        
        connection_string = (
            f"postgresql://{db_config.get('user', 'postgres')}:"
            f"{db_config.get('password', 'password')}@"
            f"{db_config.get('host', 'localhost')}:"
            f"{db_config.get('port', 5432)}/"
            f"{db_config.get('name', 'business_scraper')}"
        )
        
        return create_engine(connection_string, echo=False)
    
    def _create_tables(self):
        """Create database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self):
        """Get database session."""
        return self.SessionLocal()
    
    def store_business(self, business_data: Any) -> int:
        """Store business information in database."""
        session = self.get_session()
        
        try:
            # Check if business already exists
            existing_business = session.query(Business).filter(
                Business.name == business_data.name,
                Business.address == business_data.address,
                Business.location == business_data.location
            ).first()
            
            if existing_business:
                # Update existing business
                existing_business.phone = business_data.phone
                existing_business.website = business_data.website
                existing_business.rating = business_data.rating
                existing_business.review_count = business_data.review_count
                existing_business.coordinates = business_data.coordinates
                existing_business.updated_at = business_data.updated_at
                
                session.commit()
                business_id = existing_business.id
                logger.debug(f"Updated existing business: {business_data.name}")
            else:
                # Create new business
                business = Business(
                    name=business_data.name,
                    address=business_data.address,
                    phone=business_data.phone,
                    website=business_data.website,
                    rating=business_data.rating,
                    review_count=business_data.review_count,
                    business_type=business_data.business_type,
                    location=business_data.location,
                    coordinates=business_data.coordinates
                )
                
                session.add(business)
                session.commit()
                business_id = business.id
                logger.debug(f"Created new business: {business_data.name}")
            
            return business_id
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error storing business {business_data.name}: {e}")
            raise
        finally:
            session.close()
    
    def store_reviews(self, reviews: List[Dict[str, Any]]):
        """Store reviews in database."""
        session = self.get_session()
        
        try:
            for review_data in reviews:
                review = Review(
                    business_id=review_data['business_id'],
                    text=review_data['text'],
                    reviewer=review_data.get('reviewer'),
                    rating=review_data.get('rating'),
                    sentiment_score=review_data.get('sentiment_score'),
                    sentiment_label=review_data.get('sentiment_label'),
                    processed_text=review_data.get('processed_text'),
                    keywords=review_data.get('keywords')
                )
                
                session.add(review)
            
            session.commit()
            logger.debug(f"Stored {len(reviews)} reviews")
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error storing reviews: {e}")
            raise
        finally:
            session.close()
    
    def get_businesses(self, location: Optional[str] = None, business_type: Optional[str] = None) -> List[Business]:
        """Get businesses from database."""
        session = self.get_session()
        
        try:
            query = session.query(Business)
            
            if location:
                query = query.filter(Business.location.ilike(f"%{location}%"))
            
            if business_type:
                query = query.filter(Business.business_type == business_type)
            
            return query.all()
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting businesses: {e}")
            return []
        finally:
            session.close()
    
    def get_reviews(self, business_id: Optional[int] = None) -> List[Review]:
        """Get reviews from database."""
        session = self.get_session()
        
        try:
            query = session.query(Review)
            
            if business_id:
                query = query.filter(Review.business_id == business_id)
            
            return query.all()
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting reviews: {e}")
            return []
        finally:
            session.close()
    
    def create_scraping_session(self, location: str, business_type: str) -> int:
        """Create a new scraping session."""
        session = self.get_session()
        
        try:
            scraping_session = ScrapingSession(
                location=location,
                business_type=business_type
            )
            
            session.add(scraping_session)
            session.commit()
            
            return scraping_session.id
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error creating scraping session: {e}")
            raise
        finally:
            session.close()
    
    def update_scraping_session(self, session_id: int, status: str, businesses_scraped: int = 0, reviews_scraped: int = 0, error_message: str = None):
        """Update scraping session status."""
        session = self.get_session()
        
        try:
            scraping_session = session.query(ScrapingSession).filter(ScrapingSession.id == session_id).first()
            
            if scraping_session:
                scraping_session.status = status
                scraping_session.businesses_scraped = businesses_scraped
                scraping_session.reviews_scraped = reviews_scraped
                scraping_session.error_message = error_message
                
                if status == 'completed':
                    from datetime import datetime
                    scraping_session.completed_at = datetime.utcnow()
                
                session.commit()
                logger.debug(f"Updated scraping session {session_id}: {status}")
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating scraping session: {e}")
            raise
        finally:
            session.close()
    
    def store_market_analysis(self, location: str, business_type: str, analysis_type: str, results: Dict[str, Any]) -> int:
        """Store market analysis results."""
        session = self.get_session()
        
        try:
            analysis = MarketAnalysis(
                location=location,
                business_type=business_type,
                analysis_type=analysis_type,
                results=results
            )
            
            session.add(analysis)
            session.commit()
            
            return analysis.id
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error storing market analysis: {e}")
            raise
        finally:
            session.close()
    
    def get_market_analysis(self, location: Optional[str] = None, business_type: Optional[str] = None) -> List[MarketAnalysis]:
        """Get market analysis results."""
        session = self.get_session()
        
        try:
            query = session.query(MarketAnalysis)
            
            if location:
                query = query.filter(MarketAnalysis.location == location)
            
            if business_type:
                query = query.filter(MarketAnalysis.business_type == business_type)
            
            return query.order_by(MarketAnalysis.created_at.desc()).all()
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting market analysis: {e}")
            return []
        finally:
            session.close()
    
    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
