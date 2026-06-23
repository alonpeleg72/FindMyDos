"""
Base scraper class with common functionality.
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from abc import ABC, abstractmethod
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import re

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """
    Abstract base class for all scrapers.
    """

    def __init__(self, delay_range=(1, 3)):
        """
        Initialize the scraper.

        Args:
            delay_range: Tuple of (min_delay, max_delay) in seconds between requests
        """
        self.delay_range = delay_range
        self.session = requests.Session()
        # Set a user agent to appear more like a real browser
        self.session.headers.update({
            'User-Agent': 'FindMyDos/1.0 (+https://github.com/alonp/findmydos)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def _get_page(self, url: str, params: dict = None) -> Optional[BeautifulSoup]:
        """
        Fetch a web page and return a BeautifulSoup object.

        Args:
            url: URL to fetch
            params: Query parameters (optional)

        Returns:
            BeautifulSoup: Parsed HTML content or None if failed
        """
        try:
            # Be respectful - add delay between requests
            time.sleep(random.uniform(*self.delay_range))

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            # Parse with BeautifulSoup using html5lib parser
            soup = BeautifulSoup(response.content, 'html5lib')
            return soup

        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing {url}: {e}")
            return None

    def _extract_text(self, element) -> str:
        """
        Extract clean text from a BeautifulSoup element.

        Args:
            element: BeautifulSoup element

        Returns:
            str: Cleaned text content
        """
        if element is None:
            return ""

        # Get text and clean it up
        text = element.get_text()
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _is_hebrew_text(self, text: str) -> bool:
        """
        Check if text contains Hebrew characters.

        Args:
            text: Text to check

        Returns:
            bool: True if text contains Hebrew characters
        """
        hebrew_pattern = re.compile(r'[֐-׿]')
        return bool(hebrew_pattern.search(text))

    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Abstract method to scrape data from the source.

        Returns:
            List[Dict]: List of dictionaries containing scraped data
        """
        pass

    def close(self):
        """Close the session and clean up resources."""
        if self.session:
            self.session.close()