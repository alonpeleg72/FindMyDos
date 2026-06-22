"""
SQLAlchemy data models for the FindMyDos application.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Protest(Base):
    """
    Model representing a detected protest.
    """
    __tablename__ = 'protests'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    location_name = Column(String(255), nullable=False)
    location_latitude = Column(Float, nullable=True)
    location_longitude = Column(Float, nullable=True)
    affects_major_road = Column(Boolean, default=False)
    major_road_description = Column(String(255))  # e.g., "משפיע על כביש 4"
    source_url = Column(String(500), nullable=False)
    source_title = Column(String(255))
    published_at = Column(DateTime)  # When the source was published
    detected_at = Column(DateTime, default=datetime.utcnow)  # When we detected it
    is_hebrew = Column(Boolean, default=False)
    raw_text = Column(Text)  # Original text for debugging/reference

    def to_dict(self):
        """
        Convert the protest object to a dictionary for JSON serialization.

        Returns:
            dict: Dictionary representation of the protest
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'location_name': self.location_name,
            'location_latitude': self.location_latitude,
            'location_longitude': self.location_longitude,
            'affects_major_road': self.affects_major_road,
            'major_road_description': self.major_road_description,
            'source_url': self.source_url,
            'source_title': self.source_title,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'detected_at': self.detected_at.isoformat(),
            'is_hebrew': self.is_hebrew
        }

    def __repr__(self):
        return f'<Protest {self.title} at {self.location_name}>'