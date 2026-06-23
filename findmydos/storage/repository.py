"""
Data access layer using the Repository pattern.
"""

from typing import List, Optional
from sqlalchemy import desc, and_
import math
from findmydos.storage.database import get_scoped_session
from findmydos.storage.models import Protest

class ProtestRepository:
    """
    Repository for Protest data access operations.
    """

    def __init__(self):
        """Initialize the repository with a scoped session factory."""
        self.session_factory = get_scoped_session

    def get_session(self):
        """
        Get a new database session.

        Returns:
            Session: SQLAlchemy session object
        """
        return self.session_factory()

    def add(self, protest: Protest) -> Protest:
        """
        Add a new protest to the database.

        Args:
            protest: Protest object to add

        Returns:
            Protest: The added protest with ID populated
        """
        session = self.get_session()
        try:
            session.add(protest)
            session.commit()
            session.refresh(protest)
            return protest
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_by_id(self, protest_id: int) -> Optional[dict]:
        """
        Get a protest by its ID.

        Args:
            protest_id: ID of the protest to retrieve

        Returns:
            dict: Protest data as a dict if found, None otherwise
        """
        session = self.get_session()
        try:
            protest = session.query(Protest).filter(Protest.id == protest_id).first()
            return protest.to_dict() if protest else None
        finally:
            session.close()

    def get_recent(self, limit: int = 20, offset: int = 0) -> List[dict]:
        """
        Get recent protests ordered by detection time.

        Args:
            limit: Maximum number of protests to return
            offset: Number of protests to skip

        Returns:
            List[dict]: List of protest dicts
        """
        session = self.get_session()
        try:
            protests = session.query(Protest)\
                .order_by(desc(Protest.detected_at))\
                .limit(limit)\
                .offset(offset)\
                .all()
            return [p.to_dict() for p in protests]
        finally:
            session.close()

    def get_all(self) -> List[dict]:
        """
        Get all protests ordered by detection time.

        Args:
            None

        Returns:
            List[dict]: List of all protest dicts
        """
        session = self.get_session()
        try:
            protests = session.query(Protest)\
                .order_by(desc(Protest.detected_at))\
                .all()
            return [p.to_dict() for p in protests]
        finally:
            session.close()

    def get_by_location_proximity(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 1.0,
        hours: int = 24
    ) -> List[dict]:
        """
        Get protests near a specific location within a time window.
        Used for duplicate detection.

        Args:
            latitude: Latitude of the center point
            longitude: Longitude of the center point
            radius_km: Radius in kilometers to search
            hours: How many hours back to look

        Returns:
            List[dict]: List of protest dicts near the location
        """
        from datetime import datetime, timedelta

        session = self.get_session()
        try:
            # Calculate time threshold
            time_threshold = datetime.utcnow() - timedelta(hours=hours)

            # Get all protests from the time period
            protests = session.query(Protest)\
                .filter(Protest.detected_at >= time_threshold)\
                .all()

            # Filter by proximity (Haversine formula) and convert to dicts
            # while the session is still open
            nearby_protests = []
            for protest in protests:
                if protest.location_latitude is not None and protest.location_longitude is not None:
                    distance = self._haversine_distance(
                        latitude, longitude,
                        protest.location_latitude, protest.location_longitude
                    )
                    if distance <= radius_km:
                        nearby_protests.append(protest.to_dict())

            return nearby_protests
        finally:
            session.close()

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees).

        Returns:
            float: Distance in kilometers
        """
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r