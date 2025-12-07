import asyncio
import csv
import os

from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv

from config import BASE_URL
from utils.scraper_utils import get_browser_config
from utils.az_list_scraper import scrape_az_list_page
from models.venue import Anime

load_dotenv()


async def crawl_anime_az_list():
    """
    Main function to crawl anime data from the AZ-list pages.
    Extracts anime titles and their URL slugs (e.g., "jujutsu-kaisen-2nd-season").
    """
    # Initialize configurations
    browser_config = get_browser_config()
    session_id = "anime_az_list_session"

    # Initialize state variables
    page_number = 1
    all_animes = []
    seen_names = set()
    max_pages = 10000  # Limit to no of pages for testing

    csv_file = "anime_az_list.csv"

    # Load seen names from existing CSV
    if os.path.exists(csv_file):
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('title'):
                        seen_names.add(row['title'])
            print(f"Resuming: found {len(seen_names)} animes already in {csv_file}")
            
            # Estimate starting page (optional optimization) or just start from 1
            # Starting from 1 ensures we don't miss anything inserted earlier, 
            # and the scraper is fast enough to skip duplicates.
        except Exception as e:
            print(f"Error reading existing CSV: {e}")

    # Prepare for incremental writing
    try:
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = Anime.model_fields.keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Write header if file is new
            if not os.path.exists(csv_file) or os.path.getsize(csv_file) == 0:
                writer.writeheader()
            elif os.path.getsize(csv_file) > 0:
                 # Check if header exists? mostly we assume yes if we read it successfully above.
                 # If we just created it but exception happened, it might be empty.
                 # Actually, os.path.exists check covers it mostly.
                 pass

            # Start the web crawler context
            async with AsyncWebCrawler(config=browser_config) as crawler:
                while page_number <= max_pages:
                    # Fetch and process data from the current page
                    animes, should_stop = await scrape_az_list_page(
                        crawler,
                        page_number,
                        BASE_URL,
                        session_id,
                        seen_names,
                    )

                    if animes:
                        # Write immediately
                        writer.writerows(animes)
                        f.flush()
                        
                        all_animes.extend(animes) # Keep in memory just for stats or debugging?
                        print(f"Saved {len(animes)} new animes from page {page_number}")
                    else:
                        print(f"No new animes on page {page_number} (all duplicates). Continuing...")

                    if should_stop:
                        print(f"Reached end of pages at page {page_number}.")
                        break

                    page_number += 1

                    # Pause between requests to be polite and avoid rate limits
                    await asyncio.sleep(1)
                    
            if all_animes:
                print(f"Total this run: {len(all_animes)} animes.")
            else:
                print("No new animes found.")

    except Exception as e:
        print(f"Error during crawl: {e}")


async def main():
    """
    Entry point of the script.
    """
    await crawl_anime_az_list()


if __name__ == "__main__":
    asyncio.run(main())
