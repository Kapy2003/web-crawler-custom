import asyncio

from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv

from config import BASE_URL
from utils.data_utils import save_animes_to_csv
from utils.scraper_utils import get_browser_config
from utils.az_list_scraper import scrape_az_list_page

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
    max_pages = 283  # Limit to 5 pages for testing

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

            if should_stop or not animes:
                print(f"Reached end of pages at page {page_number}.")
                break

            # Add the animes from this page to the total list
            all_animes.extend(animes)
            page_number += 1

            # Pause between requests to be polite and avoid rate limits
            await asyncio.sleep(1)

    # Save the collected animes to a CSV file
    if all_animes:
        save_animes_to_csv(all_animes, "anime_az_list.csv")
        print(f"Saved {len(all_animes)} animes to 'anime_az_list.csv'.")
    else:
        print("No animes were found during the crawl.")


async def main():
    """
    Entry point of the script.
    """
    await crawl_anime_az_list()


if __name__ == "__main__":
    asyncio.run(main())
