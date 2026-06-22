"""
Scheduler for periodic scraping updates.
"""

import logging
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from findmydos.scrapers.news_scraper import NewsScraper
from findmydos.processing.protest_detector import ProtestDetector
from findmydos.processing.location_extractor import LocationExtractor
from findmydos.processing.road_impact_analyzer import RoadImpactAnalyzer
from findmydos.storage.repository import ProtestRepository
from findmydos.storage.models import Protest
from datetime import datetime

logger = logging.getLogger(__name__)

class UpdateScheduler:
    """
    Scheduler for periodically scraping and processing protest information.
    """

    def __init__(self, app=None):
        """
        Initialize the scheduler.

        Args:
            app: Flask application instance (optional)
        """
        self.scheduler = BackgroundScheduler()
        self.app = app
        self.news_scraper = NewsScraper()
        self.protest_detector = ProtestDetector()
        self.location_extractor = LocationExtractor()
        self.road_impact_analyzer = RoadImpactAnalyzer()
        self.protest_repo = ProtestRepository()

        # Register shutdown handler
        atexit.register(self.shutdown)

    def init_app(self, app):
        """
        Initialize the scheduler with a Flask application.

        Args:
            app: Flask application instance
        """
        self.app = app

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            # Get interval from app config or default to 2 hours
            interval_hours = 2
            if self.app:
                interval_hours = self.app.config.get('SCRAPING_INTERVAL_HOURS', 2)

            # Add the job
            self.scheduler.add_job(
                func=self._update_protests,
                trigger=IntervalTrigger(hours=interval_hours),
                id='protest_update_job',
                name='Update protest information',
                replace_existing=True
            )

            self.scheduler.start()
            logger.info(f"Scheduler started with {interval_hours} hour interval")

    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown")

    def _update_protests(self):
        """
        Perform a scraping update cycle.
        This method is called by the scheduler.
        """
        logger.info("Starting protest information update cycle")

        # If we have a Flask app, use its application context
        if self.app:
            with self.app.app_context():
                self._perform_update()
        else:
            # For testing or standalone operation
            self._perform_update()

    def _perform_update(self):
        """
        Perform the actual update process.
        """
        try:
            # Step 1: Scrape news sources
            logger.info("Scraping news sources...")
            scraped_articles = self.news_scraper.scrape()
            logger.info(f"Scraped {len(scraped_articles)} articles from news sources")

            # Step 2: Process each article
            new_protests_count = 0
            for article in scraped_articles:
                try:
                    protest = self._process_article(article)
                    if protest:
                        new_protests_count += 1
                except Exception as e:
                    logger.error(f"Error processing article {article.get('url', 'unknown')}: {e}")

            logger.info(f"Update cycle complete. Added {new_protests_count} new protests.")

        except Exception as e:
            logger.error(f"Error during update cycle: {e}")

    def _process_article(self, article_data: Dict[str, Any]) -> Optional[Protest]:
        """
        Process a scraped article to determine if it represents a new protest.

        Args:
            article_data: Dictionary containing scraped article data

        Returns:
            Protest: Protest object if a new protest was detected, None otherwise
        """
        # Extract text for analysis
        full_text = article_data.get('full_text', '')
        title = article_data.get('title', '')

        if not full_text and not title:
            return None

        # Combine title and text for analysis
        analysis_text = f"{title}\n{full_text}" if full_text else title

        # Step 1: Detect if it's a protest
        is_protest, protest_confidence, protest_metadata = self.protest_detector.detect_protest(analysis_text)

        if not is_protest or protest_confidence < 0.4:  # Confidence threshold
            return None

        # Step 2: Check if it's a Hasidic protest
        is_hasidic, hasidic_confidence = self.protest_detector.is_hasidic_protest(analysis_text)

        if not is_hasidic:
            logger.debug(f"Article is a protest but not Hasidic: {title[:50]}...")
            return None

        logger.info(f"Detected Hasidic protest: {title[:50]}... (confidence: {protest_confidence:.2f})")

        # Step 3: Extract location information
        locations = self.location_extractor.extract_locations(analysis_text)
        locations = self.location_extractor.enhance_locations_with_geocoding(locations)

        # Use the first location with coordinates, or the first location if no coordinates
        location_name = None
        latitude = None
        longitude = None

        if locations:
            # Prefer a location with coordinates
            for loc in locations:
                if 'latitude' in loc and 'longitude' in loc:
                    location_name = loc['name']
                    latitude = loc['latitude']
                    longitude = loc['longitude']
                    break

            # If no coordinates found, use the first location name
            if not location_name and locations:
                location_name = locations[0]['name']

        # Step 4: Analyze road impact
        affects_major_road, road_description = self.road_impact_analyzer.analyze_road_impact(
            analysis_text, location_name, latitude, longitude
        )

        # Step 5: Check if this is likely a duplicate of an existing protest
        if latitude is not None and longitude is not None:
            recent_protests = self.protest_repo.get_by_location_proximity(
                latitude, longitude, radius_km=0.5, hours=24
            )
            if recent_protests:
                logger.info(f"Skipping likely duplicate protest near {location_name}")
                return None

        # Step 6: Create and save the protest object
        protest = Protest(
            title=title[:255],  # Limit title length
            description=full_text[:1000] if full_text else None,  # Limit description
            location_name=location_name or "מיקום לא ידוע",
            location_latitude=latitude,
            location_longitude=longitude,
            affects_major_road=affects_major_road,
            major_road_description=road_description,
            source_url=article_data.get('url', ''),
            source_title=article_data.get('source_name', ''),
            published_at=article_data.get('published_at'),
            detected_at=datetime.utcnow(),
            is_hebrew=protest_metadata.get('has_hebrew', False),
            raw_text=analysis_text[:2000]  # Limit raw text storage
        )

        # Save to database
        saved_protest = self.protest_repo.add(protest)
        logger.info(f"Saved new protest: {saved_protest.title}")

        return saved_protest