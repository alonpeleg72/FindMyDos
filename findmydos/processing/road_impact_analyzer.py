"""
Road impact analysis module for determining if protests affect major roads.
"""

import re
import logging
import math
from typing import List, Dict, Any, Optional, Tuple
from .location_extractor import LocationExtractor

logger = logging.getLogger(__name__)

class RoadImpactAnalyzer:
    """
    Analyzes whether a protest location affects major roads.
    """

    def __init__(self, buffer_km: float = 0.5):
        """
        Initialize the road impact analyzer.

        Args:
            buffer_km: Buffer distance in kilometers to consider a protest as affecting a road
        """
        self.buffer_km = buffer_km
        self.location_extractor = LocationExtractor()

        # Major roads in Israel (simplified representation)
        # In a real implementation, we would use actual GIS data or a proper map service
        self.major_roads = {
            'כביש 1': [  # Jerusalem-Tel Aviv highway
                {'name': 'תל אביב-ירושלים', 'points': [
                    (32.0853, 34.7818),  # Tel Aviv
                    (31.7683, 35.2137)   # Jerusalem
                ]},
                {'name': 'מקטע צפוני', 'points': [
                    (32.1656, 34.8456),  # Herzliya
                    (32.0853, 34.7818)   # Tel Aviv
                ]}
            ],
            'כביש 4': [  # Coastal highway
                {'name': 'מקטע צפוני', 'points': [
                    (33.2788, 35.5657),  # Nahariya area
                    (32.7940, 34.9896)   # Haifa
                ]},
                {'name': 'מקטע מרכזי', 'points': [
                    (32.7940, 34.9896),  # Haifa
                    (32.0853, 34.7818)   # Tel Aviv
                ]},
                {'name': 'מקטע דרומי', 'points': [
                    (32.0853, 34.7818),  # Tel Aviv
                    (31.2518, 34.7913)   # Beersheba
                ]}
            ],
            'כביש 6': [  # Trans-Israel highway
                {'name': 'מקטע צפוני', 'points': [
                    (32.7940, 34.9896),  # Haifa area
                    (32.1849, 34.9074)   # Kfar Saba
                ]},
                {'name': 'מקטע מרכזי', 'points': [
                    (32.1849, 34.9074),  # Kfar Saba
                    (32.0954, 34.8854)   # Petah Tikva
                ]},
                {'name': 'מקטע דרומי', 'points': [
                    (32.0954, 34.8854),  # Petah Tikva
                    (31.8840, 35.0111)   # Modiin
                ]}
            ],
            'כביש 20': [  # Ayalon Highway (Tel Aviv)
                {'name': 'כביש 20', 'points': [
                    (32.1053, 34.7918),  # North Tel Aviv
                    (32.0453, 34.7718)   # South Tel Aviv
                ]}
            ]
        }

        # Keywords that indicate road impact in Hebrew
        self.road_impact_keywords_hebrew = {
            'כביש', 'צומת', 'דרך', 'שדרות', 'רחוב', 'מסילה',
            'פקק', 'עומס', 'שיבוש תנועה', 'חסימת כביש',
            'סגירת צומת', 'הפסקת תנועה', 'נתיב חסום'
        }

        # Keywords that indicate road impact in English
        self.road_impact_keywords_english = {
            'road', 'highway', 'street', 'avenue', 'route',
            'traffic', 'congestion', 'closure', 'blocked',
            'shutdown', 'disruption', 'gridlock'
        }

    def analyze_road_impact(self, text: str, location_name: str = None,
                          latitude: float = None, longitude: float = None) -> Tuple[bool, str]:
        """
        Analyze if a protest affects major roads based on text and location.

        Args:
            text: The protest-related text to analyze
            location_name: Name of the protest location (optional)
            latitude: Latitude of the protest location (optional)
            longitude: Longitude of the protest location (optional)

        Returns:
            Tuple[bool, str]: (affects_major_road, description)
        """
        # First, check for explicit road impact mentions in the text
        text_impact, text_description = self._check_text_for_road_impact(text)
        if text_impact:
            return (text_impact, text_description)

        # If we have location coordinates, check proximity to major roads
        if latitude is not None and longitude is not None:
            location_impact, location_description = self._check_proximity_to_roads(
                latitude, longitude
            )
            if location_impact:
                return (location_impact, location_description)

        # If we have a location name, try to geocode it and then check proximity
        if location_name and (latitude is None or longitude is None):
            coords = self._geocode_location_name(location_name)
            if coords:
                lat, lon = coords
                location_impact, location_description = self._check_proximity_to_roads(
                    lat, lon
                )
                if location_impact:
                    return (location_impact, location_description)

        # Default: no significant road impact detected
        return (False, "לא משפיע על כבישים ראשיים")

    def _check_text_for_road_impact(self, text: str) -> Tuple[bool, str]:
        """
        Check if the text explicitly mentions road impact.

        Args:
            text: Text to analyze

        Returns:
            Tuple[bool, str]: (has_impact, description)
        """
        if not text:
            return (False, "")

        text_lower = text.lower()

        # Check Hebrew keywords
        hebrew_matches = [
            keyword for keyword in self.road_impact_keywords_hebrew
            if keyword in text
        ]

        # Check English keywords
        english_matches = [
            keyword for keyword in self.road_impact_keywords_english
            if keyword in text_lower
        ]

        all_matches = hebrew_matches + english_matches

        if all_matches:
            # Try to extract which road is mentioned
            road_mentioned = self._extract_road_mention(text)
            if road_mentioned:
                return (True, f"משפיע על {road_mentioned}")
            else:
                return (True, "משפיע על תנועה בכבישים")

        return (False, "")

    def _extract_road_mention(self, text: str) -> Optional[str]:
        """
        Extract which specific road is mentioned in the text.

        Args:
            text: Text to analyze

        Returns:
            Optional[str]: Name of the road mentioned, or None
        """
        # Look for patterns like "כביש 4", "נתיב איילון", etc.
        road_patterns = [
            r'כביש\s+\d+',  # Highway number
            r'נתיב\s+\w+',  # Named highway (like נתיב איילון)
            r'שדרות\s+\w+',  # Streets
            r'רחוב\s+\w+',   # Streets
        ]

        for pattern in road_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return None

    def _check_proximity_to_roads(self, latitude: float, longitude: float) -> Tuple[bool, str]:
        """
        Check if a location is near any major roads.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location

        Returns:
            Tuple[bool, str]: (is_near_road, description)
        """
        closest_road = None
        min_distance = float('inf')

        # Check proximity to each major road segment
        for road_name, segments in self.major_roads.items():
            for segment in segments:
                distance = self._distance_to_line_segment(
                    latitude, longitude, segment['points']
                )
                if distance < min_distance:
                    min_distance = distance
                    closest_road = road_name

        # If within buffer distance, consider it as affecting the road
        if min_distance <= self.buffer_km:
            return (True, f"משפיע על {closest_road}")
        else:
            return (False, "")

    def _distance_to_line_segment(self, lat: float, lon: float,
                                points: List[Tuple[float, float]]) -> float:
        """
        Calculate the minimum distance from a point to a line segment.
        Simplified calculation - in reality, we'd use proper geospatial calculations.

        Args:
            lat: Latitude of the point
            lon: Longitude of the point
            points: List of (lat, lon) points defining the line segment

        Returns:
            float: Distance in kilometers (approximate)
        """
        if len(points) < 2:
            # If we only have one point, calculate distance to that point
            if points:
                return self._haversine_distance(lat, lon, points[0][0], points[0][1])
            return float('inf')

        # For multiple points, find the minimum distance to any segment
        min_dist = float('inf')
        for i in range(len(points) - 1):
            dist = self._distance_to_segment(lat, lon, points[i], points[i+1])
            if dist < min_dist:
                min_dist = dist

        return min_dist

    def _distance_to_segment(self, lat: float, lon: float,
                           point1: Tuple[float, float],
                           point2: Tuple[float, float]) -> float:
        """
        Calculate distance from a point to a line segment.
        Simplified approximation.

        Args:
            lat: Latitude of the point
            lon: Longitude of the point
            point1: First point of the segment (lat, lon)
            point2: Second point of the segment (lat, lon)

        Returns:
            float: Distance in kilometers (approximate)
        """
        # Convert to Cartesian coordinates for simplicity (approximation)
        # In a real implementation, we'd use proper spherical geometry
        try:
            # Simple Euclidean distance approximation (not accurate for large distances)
            # but OK for small distances within a city
            x1, y1 = point1[1] * math.cos(math.radians(point1[0])), point1[0]
            x2, y2 = point2[1] * math.cos(math.radians(point2[0])), point2[0]
            x0, y0 = lon * math.cos(math.radians(lat)), lat

            # Calculate distance from point to line segment
            # Vector math: distance = |(P2-P1) x (P1-P0)| / |P2-P1|
            dx = x2 - x1
            dy = y2 - y1
            if dx == 0 and dy == 0:
                # Segment is actually a point
                return math.sqrt((x0 - x1)**2 + (y0 - y1)**2)

            # Parameter t where projection of P0 onto the line falls
            t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx * dx + dy * dy)
            t = max(0, min(1, t))  # Clamp to [0, 1]

            # Find closest point on the segment
            closest_x = x1 + t * dx
            closest_y = y1 + t * dy

            # Return distance
            return math.sqrt((x0 - closest_x)**2 + (y0 - closest_y)**2) * 111  # Rough conversion to km
        except Exception as e:
            logger.warning(f"Error calculating distance to segment: {e}")
            return float('inf')

    def _haversine_distance(self, lat1: float, lon1: float,
                          lat2: float, lon2: float) -> float:
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

    def _geocode_location_name(self, location_name: str) -> Optional[Tuple[float, float]]:
        """
        Geocode a location name to get coordinates.

        Args:
            location_name: Name of the location to geocode

        Returns:
            Tuple[float, float]: (latitude, longitude) or None if failed
        """
        try:
            # Use the location extractor's geocoder
            return self.location_extractor.geocode_location(location_name)
        except Exception as e:
            logger.error(f"Error geocoding location {location_name}: {e}")
            return None