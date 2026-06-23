"""
Location extraction module using NER and geocoding.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

# Import locally to avoid circular dependencies
from .language_detector import LanguageDetector

logger = logging.getLogger(__name__)

class LocationExtractor:
    """
    Extracts location information from text using NER and geocoding.
    """

    def __init__(self, user_agent: str = "findmydos/1.0", timeout: int = 10):
        """
        Initialize the location extractor.

        Args:
            user_agent: User agent string for geocoding service
            timeout: Timeout for geocoding requests in seconds
        """
        self.geocoder = Nominatim(user_agent=user_agent, timeout=timeout)
        self.language_detector = LanguageDetector()

        # Common Israeli cities and locations for fallback matching
        self.known_locations = {
            'ירושלים': (31.7683, 35.2137),
            'תל אביב': (32.0853, 34.7818),
            'חיפה': (32.7940, 34.9896),
            'בני ברק': (32.0959, 34.8926),
            'חולון': (32.0108, 34.7675),
            'בת ים': (32.0303, 34.7622),
            'פתח תקווה': (32.0954, 34.8854),
            'אשדוד': (31.7927, 34.6476),
            'נתניה': (32.3259, 34.8618),
            'באר שבע': (31.2518, 34.7913),
            'הרצליה': (32.1656, 34.8456),
            'רחובות': (31.8985, 34.8091),
            'כפר סבא': (32.1849, 34.9074),
            'הרדוף': (32.4689, 35.0004),
            'מודיעין': (31.8840, 35.0111),
            'לוד': (31.9455, 34.8852),
            'רמלה': (31.9285, 34.8283),
            'אילת': (29.5581, 34.9482),
            'טבריה': (32.7891, 35.5241),
            'צפת': (32.9679, 35.4943),
            'קריית שמונה': (33.2788, 35.5657),
        }

        # Common Hebrew location prefixes/suffixes
        self.location_prefixes = ['ב', 'במא', 'ל', 'אל', 'מע']
        self.location_suffixes = ['ה', 'ים', 'ים', 'ית']

    def extract_locations(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract location information from text.

        Args:
            text: Text to analyze for location information

        Returns:
            List[Dict]: List of location dictionaries with name, coordinates, and confidence
        """
        if not text or not text.strip():
            return []

        locations = []

        # First, try to find locations using known location matching
        known_locations = self._extract_known_locations(text)
        locations.extend(known_locations)

        # For a more sophisticated implementation, we would use NER here
        # For now, we'll rely on known locations and regex patterns

        # Look for location patterns in Hebrew text
        pattern_locations = self._extract_pattern_locations(text)
        locations.extend(pattern_locations)

        # Deduplicate locations by name (keeping the one with highest confidence)
        unique_locations = self._deduplicate_locations(locations)

        return unique_locations

    def _extract_known_locations(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract locations by matching against known Israeli cities.

        Args:
            text: Text to search

        Returns:
            List[Dict]: List of location dictionaries
        """
        locations = []

        for location_name, (lat, lon) in self.known_locations.items():
            # Check for the location name in the text
            # Use word boundaries to avoid partial matches
            pattern = rf'\b{re.escape(location_name)}\b'
            if re.search(pattern, text):
                locations.append({
                    'name': location_name,
                    'latitude': lat,
                    'longitude': lon,
                    'confidence': 0.9,  # High confidence for exact matches
                    'source': 'known_locations'
                })

        return locations

    def _extract_pattern_locations(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract locations using common Hebrew location patterns.

        Args:
            text: Text to analyze

        Returns:
            List[Dict]: List of location dictionaries
        """
        locations = []

        # Pattern for locations with common prefixes/suffixes
        # This is a simplified approach - a real implementation would use NER
        hebrew_words = re.findall(r'\b[א-ת]+\\b', text)

        for word in hebrew_words:
            # Skip very short words
            if len(word) < 2:
                continue

            # Check if this looks like a location name
            # In a real implementation, we'd use NER or a gazetteer
            # For now, we'll check if adding common location words makes a known location
            for base_name, (lat, lon) in self.known_locations.items():
                # Check if the word is part of a known location or vice versa
                if word in base_name or base_name in word:
                    if len(word) >= 2:  # Avoid single characters
                        locations.append({
                            'name': word,
                            'latitude': lat,
                            'longitude': lon,
                            'confidence': 0.6,  # Lower confidence for pattern matches
                            'source': 'pattern_matching'
                        })

        return locations

    def geocode_location(self, location_name: str) -> Optional[Tuple[float, float]]:
        """
        Geocode a location name to get latitude and longitude.

        Args:
            location_name: Name of the location to geocode

        Returns:
            Tuple[float, float]: (latitude, longitude) or None if failed
        """
        try:
            # Add "Israel" to improve geocoding accuracy for local locations
            query = f"{location_name}, Israel"
            location = self.geocoder.geocode(query)

            if location:
                return (location.latitude, location.longitude)
            else:
                # Try without "Israel" if that failed
                location = self.geocoder.geocode(location_name)
                if location:
                    return (location.latitude, location.longitude)

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Geocoding timeout or service error for {location_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error geocoding {location_name}: {e}")

        # Rate limiting - be nice to the geocoding service
        time.sleep(1)

        return None

    def enhance_locations_with_geocoding(self, locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance location dictionaries with geocoded coordinates.

        Args:
            locations: List of location dictionaries (may already have coordinates)

        Returns:
            List[Dict]: List of location dictionaries with coordinates
        """
        enhanced_locations = []

        for location in locations:
            # If we already have coordinates, use them
            if 'latitude' in location and 'longitude' in location:
                enhanced_locations.append(location)
                continue

            # Otherwise, try to geocode
            location_name = location.get('name')
            if location_name:
                coords = self.geocode_location(location_name)
                if coords:
                    lat, lon = coords
                    enhanced_location = location.copy()
                    enhanced_location['latitude'] = lat
                    enhanced_location['longitude'] = lon
                    enhanced_location['geocoded'] = True
                    enhanced_locations.append(enhanced_location)
                else:
                    # Keep the location even if we couldn't geocode it
                    enhanced_locations.append(location)
            else:
                enhanced_locations.append(location)

        return enhanced_locations

    def _deduplicate_locations(self, locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate locations by name, keeping the one with highest confidence.

        Args:
            locations: List of location dictionaries

        Returns:
            List[Dict]: Deduplicated list of location dictionaries
        """
        # Group by location name
        grouped = {}
        for location in locations:
            name = location.get('name', '').lower().strip()
            if not name:
                continue

            if name not in grouped:
                grouped[name] = []
            grouped[name].append(location)

        # For each group, keep the location with highest confidence
        deduped = []
        for name, loc_list in grouped.items():
            if loc_list:
                # Sort by confidence descending
                best_location = max(loc_list, key=lambda x: x.get('confidence', 0))
                deduped.append(best_location)

        return deduped