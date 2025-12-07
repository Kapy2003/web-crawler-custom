import asyncio
import csv
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from utils.iframe_extractor import extract_iframe_src


async def fetch_episode_iframes(
    crawler: AsyncWebCrawler,
    anime_slug: str,
    episode_num: int = 1,
    session_id: str = "iframe_session",
) -> str:
    """
    Fetches an episode page and extracts the iframe src.
    
    Args:
        crawler (AsyncWebCrawler): The web crawler instance.
        anime_slug (str): The anime slug (e.g., "jujutsu-kaisen-2nd-season").
        episode_num (int): The episode number to fetch (default: 1).
        session_id (str): The session identifier.
    
    Returns:
        str: The iframe src URL if found, empty string otherwise.
    """
    url = f"https://hianimez.live/watch/{anime_slug}/ep-{episode_num}"
    
    try:
        result = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                session_id=session_id,
            ),
        )
        
        if result.success:
            iframe_src = extract_iframe_src(result.html)
            if iframe_src:
                print(f"✓ Found iframe for {anime_slug} ep-{episode_num}")
                return iframe_src
            else:
                print(f"✗ No iframe found for {anime_slug} ep-{episode_num}")
        else:
            print(f"✗ Failed to fetch {url}: {result.error_message}")
    except Exception as e:
        print(f"✗ Error fetching {url}: {e}")
    
    return ""


async def enrich_anime_with_iframes(
    csv_input_file: str,
    csv_output_file: str,
    max_episodes: int = 283,
) -> None:
    """
    Reads anime from CSV and fetches iframe URLs for first episode of each anime.
    
    Args:
        csv_input_file (str): Path to input CSV file.
        csv_output_file (str): Path to output CSV file with embed_url column.
        max_episodes (int): Maximum number of episodes to attempt (for pagination).
    """
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        verbose=False,
    )
    
    animes = []
    
    # Read input CSV
    try:
        with open(csv_input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            animes = list(reader)
        print(f"Loaded {len(animes)} anime from {csv_input_file}")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    
    # Fetch iframes
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for idx, anime in enumerate(animes, 1):
            slug = anime.get('slug', '')
            
            if not slug:
                print(f"[{idx}/{len(animes)}] Skipping anime with no slug")
                continue
            
            print(f"[{idx}/{len(animes)}] Fetching iframe for {slug}...")
            
            # Try to get iframe from episode 1
            embed_url = await fetch_episode_iframes(
                crawler,
                slug,
                episode_num=1,
                session_id="iframe_session",
            )
            
            anime['embed_url'] = embed_url
            
            # Rate limiting
            await asyncio.sleep(0.5)
    
    # Write output CSV
    try:
        fieldnames = list(animes[0].keys()) if animes else []
        
        with open(csv_output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(animes)
        
        print(f"\nSaved {len(animes)} anime with embed URLs to {csv_output_file}")
    except Exception as e:
        print(f"Error writing CSV: {e}")


async def main():
    """
    Main function to enrich anime data with iframe URLs.
    """
    await enrich_anime_with_iframes(
        csv_input_file="anime_az_list.csv",
        csv_output_file="anime_az_list_with_iframes.csv",
    )


if __name__ == "__main__":
    asyncio.run(main())
