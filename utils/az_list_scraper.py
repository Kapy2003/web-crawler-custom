import asyncio
import re
from typing import List, Set, Tuple
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

from models.venue import Anime
from utils.data_utils import is_duplicate_anime


def extract_anime_from_html(html_content: str) -> List[dict]:
    """
    Extracts anime titles and slugs from the AZ-list page HTML.
    
    Args:
        html_content (str): The HTML content to parse.
    
    Returns:
        List[dict]: List of anime with title and slug extracted from links.
    """
    animes = []
    seen_slugs = set()  # Avoid duplicate slugs on the same page
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all anime links - they're in format like:
        # <a href="https://hianimez.live/watch/jujutsu-kaisen-2nd-season">Jujutsu Kaisen 2nd Season</a>
        anime_links = soup.find_all('a', href=re.compile(r'/watch/[a-zA-Z0-9\-]+$'))
        
        for link in anime_links:
            href = link.get('href', '')
            title = link.get_text(strip=True)
            
            # Skip empty titles or common non-anime links
            if not title or title.isdigit():
                continue
            
            # Extract slug from URL (e.g., "/watch/jujutsu-kaisen-2nd-season" -> "jujutsu-kaisen-2nd-season")
            match = re.search(r'/watch/([a-zA-Z0-9\-]+)$', href)
            if match:
                slug = match.group(1)
                
                # Skip if we already have this slug on this page
                if slug in seen_slugs:
                    continue
                    
                seen_slugs.add(slug)
                anime = {
                    'title': title,
                    'slug': slug,
                    'watch_url': href,
                    'rating': 'N/A',
                    'resolution': 'N/A',
                    'year': 'N/A',
                    'description': '',
                }
                animes.append(anime)
    except Exception as e:
        print(f"Error extracting anime from HTML: {e}")
    
    return animes


async def scrape_az_list_page(
    crawler: AsyncWebCrawler,
    page_number: int,
    base_url: str,
    session_id: str,
    seen_names: Set[str],
) -> Tuple[List[dict], bool]:
    """
    Scrapes a single page from the AZ-list and extracts anime with slugs.
    
    Args:
        crawler (AsyncWebCrawler): The web crawler instance.
        page_number (int): The page number to fetch.
        base_url (str): The base URL of the website.
        session_id (str): The session identifier.
        seen_names (Set[str]): Set of anime names that have already been seen.
    
    Returns:
        Tuple[List[dict], bool]:
            - List[dict]: A list of anime with titles and slugs.
            - bool: A flag indicating if we should stop (no more pages).
    """
    url = f"{base_url}?page={page_number}"
    print(f"Loading page {page_number}...")
    
    # Fetch the page
    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id=session_id,
        ),
    )
    
    if not result.success:
        print(f"Error fetching page {page_number}: {result.error_message}")
        return [], True
    
    # Extract anime from HTML
    extracted_animes = extract_anime_from_html(result.html)
    
    if not extracted_animes:
        print(f"No animes found on page {page_number}.")
        return [], True
    
    # Remove duplicates
    unique_animes = []
    for anime in extracted_animes:
        if not is_duplicate_anime(anime["title"], seen_names):
            seen_names.add(anime["title"])
            unique_animes.append(anime)
        else:
            print(f"Duplicate anime '{anime['title']}' found. Skipping.")
    
    print(f"Extracted {len(unique_animes)} unique animes from page {page_number}.")
    return unique_animes, False
