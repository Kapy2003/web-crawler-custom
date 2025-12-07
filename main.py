import asyncio

from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv

from config import BASE_URL, CSS_SELECTOR, REQUIRED_KEYS
from utils.data_utils import (
    save_animes_to_csv,
)
from utils.scraper_utils import (
    fetch_and_process_page,
    get_browser_config,
    get_llm_strategy,
)

load_dotenv()


async def crawl_animes():
    """
    Main function to crawl anime data from the website.
    """
    # Initialize configurations
    browser_config = get_browser_config()
    llm_strategy = get_llm_strategy()
    session_id = "anime_crawl_session"

    # Initialize state variables
    page_number = 1
    all_animes = []
    seen_names = set()

    # Start the web crawler context
    # https://docs.crawl4ai.com/api/async-webcrawler/#asyncwebcrawler
    async with AsyncWebCrawler(config=browser_config) as crawler:
        while True:
            # Fetch and process data from the current page
            animes, no_results_found = await fetch_and_process_page(
                crawler,
                page_number,
                BASE_URL,
                CSS_SELECTOR,
                llm_strategy,
                session_id,
                REQUIRED_KEYS,
                seen_names,
            )

            if no_results_found:
                print("No more animes found. Ending crawl.")
                break  # Stop crawling when "No Results Found" message appears

            if not animes:
                print(f"No animes extracted from page {page_number}.")
                break  # Stop if no animes are extracted

            # Add the animes from this page to the total list
            all_animes.extend(animes)
            page_number += 1  # Move to the next page

            # Pause between requests to be polite and avoid rate limits
            await asyncio.sleep(2)  # Adjust sleep time as needed

    # Save the collected animes to a CSV file
    if all_animes:
        save_animes_to_csv(all_animes, "complete_animes.csv")
        print(f"Saved {len(all_animes)} animes to 'complete_animes.csv'.")
    else:
        print("No animes were found during the crawl.")

    # Display usage statistics for the LLM strategy
    llm_strategy.show_usage()


async def main():
    """
    Entry point of the script.
    """
    await crawl_animes()


if __name__ == "__main__":
    asyncio.run(main())
