"""
Test script for the FindMyDos processing pipeline.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from findmydos.processing.language_detector import LanguageDetector
from findmydos.processing.protest_detector import ProtestDetector
from findmydos.processing.location_extractor import LocationExtractor
from findmydos.processing.road_impact_analyzer import RoadImpactAnalyzer
from findmydos.storage.models import Protest, Base
from findmydos.storage.repository import ProtestRepository
from findmydos.storage.database import get_engine, init_db
from datetime import datetime

def test_full_pipeline():
    """Test the full processing pipeline with sample data."""
    print("=== Testing FindMyDos Processing Pipeline ===\n")

    # Initialize components
    lang_detector = LanguageDetector()
    protest_detector = ProtestDetector()
    location_extractor = LocationExtractor()
    road_impact_analyzer = RoadImpactAnalyzer()

    # Test Hebrew protest text with known locations
    sample_text = """
    הפגנה חרדית גדולה של אלפי מפגינים מירושלים ובני ברק יצאה לרחובות
    במחאה נגד גיוס חרדים לצה״ל. המפגינים חוסמים את הכביש 4 בצומת תל אביב
    וגורמים לפקק תנועה כבד באזור. משטרה מגיעה למקום ומבקרת את הדרך.
    """

    print("1. Testing language detection...")
    is_hebrew, hebrew_confidence = lang_detector.detect_language(sample_text)
    print(f"   Is Hebrew: {is_hebrew} (confidence: {hebrew_confidence:.2f})")

    print("\n2. Testing protest detection...")
    is_protest, protest_confidence, protest_metadata = protest_detector.detect_protest(sample_text)
    print(f"   Is protest: {is_protest} (confidence: {protest_confidence:.2f})")
    print(f"   Hasidic matches: {protest_metadata.get('hasidic_matches', 0)}")
    print(f"   Location indicators found: {protest_metadata.get('location_indicators_found', False)}")

    print("\n3. Testing Hasidic protest detection...")
    is_hasidic, hasidic_confidence = protest_detector.is_hasidic_protest(sample_text)
    print(f"   Is Hasidic protest: {is_hasidic} (confidence: {hasidic_confidence:.2f})")

    if not (is_protest and is_hasidic):
        print("   ERROR: Sample text should be detected as a Hasidic protest!")
        return False

    print("\n4. Testing location extraction...")
    locations = location_extractor.extract_locations(sample_text)
    print(f"   Found {len(locations)} potential locations:")
    for loc in locations:
        print(f"     - {loc['name']} (confidence: {loc['confidence']:.2f})")

    # Enhance with geocoding
    if locations:
        print("\n5. Testing geocoding...")
        enhanced_locations = location_extractor.enhance_locations_with_geocoding(locations)
        geocoded_locations = [loc for loc in enhanced_locations if 'latitude' in loc and 'longitude' in loc]
        print(f"   Successfully geocoded {len(geocoded_locations)} locations:")
        for loc in geocoded_locations:
            print(f"     - {loc['name']}: ({loc['latitude']:.4f}, {loc['longitude']:.4f})")

    print("\n6. Testing road impact analysis...")
    # Use the first geocoded location if available, otherwise use text analysis
    test_lat, test_lon = None, None
    test_location_name = None

    if locations:
        # Try to get coordinates from the first location
        first_loc = locations[0]
        coords = location_extractor.geocode_location(first_loc['name'])
        if coords:
            test_lat, test_lon = coords
            test_location_name = first_loc['name']

    affects_road, road_description = road_impact_analyzer.analyze_road_impact(
        sample_text, test_location_name, test_lat, test_lon
    )
    print(f"   Affects major road: {affects_road}")
    print(f"   Description: {road_description}")

    print("\n7. Testing database storage...")
    try:
        # Initialize database (create tables)
        init_db()

        # Create a protest object
        protest = Protest(
            title="הפגנה חרדית נגד גיוס לצה״ל",
            description="הפגנה חרדית גדולה בירושלים ובני ברק במחאה נגד גיוס חרדים לצה״ל",
            location_name="ירושלים",
            location_latitude=31.7683,
            location_longitude=35.2137,
            affects_major_road=True,
            major_road_description="משפיע על כביש 4",
            source_url="https://example.com/protest-article",
            source_title="דוגמה למקור מידע",
            published_at=datetime.now(),
            detected_at=datetime.now(),
            is_hebrew=True,
            raw_text=sample_text[:500]  # Limit length
        )

        # Save to database
        repo = ProtestRepository()
        saved_protest = repo.add(protest)
        print(f"   Successfully saved protest with ID: {saved_protest.id}")

        # Retrieve it
        retrieved_protest = repo.get_by_id(saved_protest.id)
        if retrieved_protest:
            print(f"   Successfully retrieved protest: {retrieved_protest.title}")
        else:
            print("   ERROR: Failed to retrieved protest!")
            return False

        # Check for duplicates (should not find this protest as a duplicate of itself with different params)
        try:
            nearby = repo.get_by_location_proximity(
                31.7683, 35.2137, radius_km=0.1, hours=1
            )
            print(f"   Found {len(nearby)} nearby protests (should be 1 - the one we just added)")
        except Exception as e:
            print(f"   ERROR in duplicate check: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"   ERROR in database operations: {e}")
        return False

    print("\n=== All tests passed! ===")
    return True

if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)