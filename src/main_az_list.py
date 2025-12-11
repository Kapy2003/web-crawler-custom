import asyncio
import csv
import os
import re
from typing import List, Set, Tuple
from bs4 import BeautifulSoup

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from dotenv import load_dotenv

from config import BASE_URL
from utils.scraper_utils import get_browser_config
from utils.data_utils import is_duplicate_anime
from models.venue import Anime

load_dotenv()

# --- FIXED LOGIC INLINED FROM utils.az_list_scraper ---

def extract_anime_from_html(html_content: str) -> List[dict]:
    """
    Extracts anime titles and slugs from the AZ-list page HTML.
    FIXED: Prevents merging of metadata (like 'TV', '12 Eps') into the title.
    """
    animes = []
    seen_slugs = set()
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        anime_links = soup.find_all('a', href=re.compile(r'/watch/[a-zA-Z0-9\-]+$'))
        
        for link in anime_links:
            href = link.get('href', '')
            
            # --- FIX VARIANT 1: Use separator ---
            # link.get_text(separator='|', strip=True) will return "Title|TV|12 Eps"
            # We then split by '|' and take the first part.
            full_text = link.get_text(separator='|', strip=True)
            if not full_text:
                continue
                
            parts = full_text.split('|')
            title = parts[0].strip()
            
            # If title is empty or just digits (sometimes happens if structure is weird), try next part?
            # But usually the first text node is the title.
            if not title or title.isdigit():
                # Fallback: try iterating children to find the first text node explicitly
                for child in link.children:
                    if isinstance(child, str) and child.strip():
                        title = child.strip()
                        break
            
            if not title or title.isdigit():
                 continue

            # Extract slug from URL
            match = re.search(r'/watch/([a-zA-Z0-9\-]+)$', href)
            if match:
                slug = match.group(1)
                
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
    Uses the FIXED extract_anime_from_html function.
    """
    url = f"{base_url}?page={page_number}"
    print(f"Loading page {page_number}...")
    
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
    
    extracted_animes = extract_anime_from_html(result.html)
    
    if not extracted_animes:
        print(f"No animes found on page {page_number}.")
        return [], True
    
    unique_animes = []
    for anime in extracted_animes:
        if not is_duplicate_anime(anime["title"], seen_names):
            seen_names.add(anime["title"])
            unique_animes.append(anime)
        else:
            # print(f"Duplicate anime '{anime['title']}' found. Skipping.")
            pass
    
    print(f"Extracted {len(unique_animes)} unique animes from page {page_number}.")
    return unique_animes, False

# --- END FIXED LOGIC ---

async def crawl_anime_az_list():
    # Initialize configurations
    browser_config = get_browser_config()
    session_id = "anime_az_list_session_fixed"

    # Initialize state variables
    page_number = 1
    all_animes = []
    seen_names = set()
    max_pages = 10000 

    # Robust path resolution
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_file = os.path.join(base_dir, "data", "csvs", "anime_az_list.csv")
    # Or should we append to the existing one? Use a new one to be safe.

    # Load seen names if file exists (optional, to resume)
    if os.path.exists(csv_file):
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('title'):
                        seen_names.add(row['title'])
            print(f"Resuming: found {len(seen_names)} animes already in {csv_file}")
        except Exception as e:
            print(f"Error reading existing CSV: {e}")

    # Prepare for incremental writing
    try:
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = Anime.model_fields.keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not os.path.exists(csv_file) or os.path.getsize(csv_file) == 0:
                writer.writeheader()

            async with AsyncWebCrawler(config=browser_config) as crawler:
                while page_number <= max_pages:
                    animes, should_stop = await scrape_az_list_page(
                        crawler,
                        page_number,
                        BASE_URL,
                        session_id,
                        seen_names,
                    )

                    if animes:
                        writer.writerows(animes)
                        f.flush()
                        all_animes.extend(animes)
                        print(f"Saved {len(animes)} new animes from page {page_number}")
                    else:
                        print(f"No new animes on page {page_number} (all duplicates). Continuing...")

                    if should_stop:
                        print(f"Reached end of pages at page {page_number}.")
                        break

                    page_number += 1
                    await asyncio.sleep(1)
                    
            if all_animes:
                print(f"Total this run: {len(all_animes)} animes.")
            else:
                print("No new animes found.")

    except Exception as e:
        print(f"Error during crawl: {e}")

async def main():
    await crawl_anime_az_list()

if __name__ == "__main__":
    asyncio.run(main())
