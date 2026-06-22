"""
News scraper implementation for Israeli news sites.
"""

"""
News scraper implementation for Israeli news sites.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class NewsScraper(BaseScraper):
    """
    Scraper for Israeli news websites.
    """

    def __init__(self, delay_range=(2, 5)):
        """
        Initialize the news scraper.

        Args:
            delay_range: Tuple of (min_delay, max_delay) in seconds between requests
        """
        super().__init__(delay_range)
        self.sources = {
            'ynet': {
                'name': 'Ynet',
                'base_url': 'https://www.ynet.co.il',
                'sections': [
                    '/category/184',  # News
                    '/category/108',  # Israel
                ]
            },
            'haaretz': {
                'name': 'Haaretz',
                'base_url': 'https://www.haaretz.co.il',
                'sections': [
                    '/news/israel/',
                    '/news/politics/'
                ]
            }
        }

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape news from configured sources for protest-related content.

        Returns:
            List[Dict]: List of protest candidate articles
        """
        protests = []

        for source_key, source_info in self.sources.items():
            try:
                logger.info(f"Scraping {source_info['name']}...")
                source_protests = self._scrape_source(source_info)
                protests.extend(source_protests)
                logger.info(f"Found {len(source_protests)} potential protests from {source_info['name']}")
            except Exception as e:
                logger.error(f"Error scraping {source_info['name']}: {e}")

        return protests

    def _scrape_source(self, source_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scrape a specific news source.

        Args:
            source_info: Dictionary containing source information

        Returns:
            List[Dict]: List of protest candidate articles from this source
        """
        protests = []
        base_url = source_info['base_url']

        for section in source_info['sections']:
            url = urljoin(base_url, section)
            soup = self._get_page(url)

            if soup is None:
                continue

            # Find article links - this will vary by site
            article_links = self._extract_article_links(soup, base_url)

            for link in article_links[:10]:  # Limit to first 10 articles per section
                try:
                    article_data = self._scrape_article(link, source_info['name'])
                    if article_data and self._is_protest_related(article_data):
                        protests.append(article_data)
                except Exception as e:
                    logger.error(f"Error processing article {link}: {e}")

        return protests

    def _extract_article_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract article links from a news page.
        Implementation will vary by site.

        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for resolving relative links

        Returns:
            List[str]: List of article URLs
        """
        links = []

        # Generic approach - look for links that seem to be articles
        # This will need to be customized for each site
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Make absolute URL
            absolute_url = urljoin(base_url, href)

            # Basic filtering - look for links that seem to be articles
            if self._looks_like_article_url(absolute_url):
                links.append(absolute_url)

        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)

        return unique_links

    def _looks_like_article_url(self, url: str) -> bool:
        """
        Heuristic to determine if a URL looks like an article.

        Args:
            url: URL to check

        Returns:
            bool: True if URL looks like an article
        """
        # Avoid common non-article URLs
        avoid_patterns = [
            r'\.(jpg|jpeg|png|gif|pdf|doc|xls)$',
            r'/tag/',
            r'/author/',
            r'/search',
            r'/login',
            r'/signup',
            r'/ads/',
            r'/wp-content/',
        ]

        for pattern in avoid_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False

        # Look for patterns that suggest articles
        article_patterns = [
            r'/article/',
            r'/news/',
            r'/\d{4}/\d{2}/\d{2}/',  # Date-based URLs
            r'/[a-z]+-\d+$',  # Slug with ID
        ]

        for pattern in article_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True

        # If we have a reasonable length path, it might be an article
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path_segments = [seg for seg in parsed.path.split('/') if seg]
        if len(path_segments) >= 2 and len(path_segments[-1]) > 10:
            return True

        return False

    def _scrape_article(self, url: str, source_name: str) -> Optional[Dict[str, Any]]:
        """
        Scrape an individual article.

        Args:
            url: URL of the article to scrape
            source_name: Name of the news source

        Returns:
            Dict: Article data or None if failed
        """
        soup = self._get_page(url)
        if soup is None:
            return None

        # Extract article data - implementation will vary by site
        title = self._extract_title(soup)
        if not title:
            return None

        # Get publication date if available
        published_at = self._extract_publish_date(soup)

        # Extract main content
        content = self._extract_content(soup)

        # Combine title and content for analysis
        full_text = f"{title}\n{content}" if content else title

        return {
            'title': title,
            'url': url,
            'source_name': source_name,
            'published_at': published_at,
            'content': content,
            'full_text': full_text,
            'source_type': 'news'
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extract article title.

        Args:
            soup: BeautifulSoup object of the article page

        Returns:
            str: Article title
        """
        # Try common title selectors
        title_selectors = [
            'h1',
            '.title',
            '.article-title',
            '[data-role="title"]',
            'meta[property="og:title"]'
        ]

        for selector in title_selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element and element.get('content'):
                    return self._extract_text(element)
            else:
                element = soup.select_one(selector)
                if element:
                    return self._extract_text(element)

        # Fallback to title tag
        title_tag = soup.find('title')
        if title_tag:
            return self._extract_text(title_tag)

        return ""

    def _extract_publish_date(self, soup: BeautifulSoup):
        """
        Extract publication date from article.

        Args:
            soup: BeautifulSoup object of the article page

        Returns:
            datetime: Publication date or None if not found
        """
        # This would need to be implemented per site
        # For now, return None and we'll use detection time
        return None

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main article content.

        Args:
            soup: BeautifulSoup object of the article page

        Returns:
            str: Article content
        """
        # Try common content selectors
        content_selectors = [
            '.article-content',
            '.content',
            '.text',
            '[data-role="content"]',
            'article',
            '.post-content'
        ]

        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Remove script and style elements
                for script in element(["script", "style"]):
                    script.decompose()
                return self._extract_text(element)

        # Fallback: get all text and hope for the best
        return self._extract_text(soup.find('body'))

    def _is_protest_related(self, article_data: Dict[str, Any]) -> bool:
        """
        Check if an article is protest-related.

        Args:
            article_data: Dictionary containing article data

        Returns:
            bool: True if article appears to be protest-related
        """
        text = article_data.get('full_text', '').lower()

        # Protest-related keywords in Hebrew and English
        protest_keywords = [
            # Hebrew
            'הפגנה', 'מחאה', 'צעדה', 'שביתה', 'פקודה',
            'תהלוכת', 'כנס חירום', 'עצרת', 'מחסום',
            # English
            'protest', 'demonstration', 'march', 'strike', 'rally',
            'demonstrators', 'protesters'
        ]

        # Check if any protest keywords appear in the text
        for keyword in protest_keywords:
            if keyword in text:
                return True

        return False