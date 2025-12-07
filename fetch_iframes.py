import csv
import json
import asyncio
import os
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
                # Less verbose failure to avoid spamming console during normal stop
                # print(f"✗ No iframe found for {anime_slug} ep-{episode_num}")
                pass
        else:
            print(f"✗ Failed to fetch {url}: {result.error_message}")
    except Exception as e:
        print(f"✗ Error fetching {url}: {e}")
    
    return ""


async def enrich_anime_with_iframes(
    csv_input_file: str,
    csv_output_file: str,
    max_episodes: int = 10000,
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
    # Check for existing progress
    processed_slugs = set()
    file_exists = os.path.exists(csv_output_file)
    
    if file_exists:
        try:
            with open(csv_output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('slug'):
                        processed_slugs.add(row['slug'])
            print(f"resuming: found {len(processed_slugs)} already processed animes.")
        except Exception as e:
            print(f"Error reading existing output file: {e}")
            return

    # Open output file in append mode
    try:
        with open(csv_output_file, 'a', newline='', encoding='utf-8') as f_out:
            fieldnames = list(animes[0].keys()) if animes else []
            if 'embed_url' not in fieldnames:
                fieldnames.append('embed_url')
            
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            
            # Write header if file didn't exist
            if not file_exists and fieldnames:
                writer.writeheader()
            
            # Fetch iframes
            async with AsyncWebCrawler(config=browser_config) as crawler:
                for idx, anime in enumerate(animes, 1):
                    slug = anime.get('slug', '')
                    
                    if not slug:
                        print(f"[{idx}/{len(animes)}] Skipping anime with no slug")
                        continue
                    
                    if slug in processed_slugs:
                        print(f"[{idx}/{len(animes)}] Skipping {slug} (already processed)")
                        continue
                    
                    print(f"[{idx}/{len(animes)}] Fetching episodes for {slug}...")
                    
                    episode_map = {}
                    for ep_num in range(1, max_episodes + 1):
                        # Try to get iframe for the current episode
                        iframe_src = await fetch_episode_iframes(
                            crawler,
                            slug,
                            episode_num=ep_num,
                            session_id="iframe_session",
                        )
                        
                        if iframe_src:
                            episode_map[str(ep_num)] = iframe_src
                        else:
                            # If we can't find episode 1, it's likely the anime isn't there or slug is wrong.
                            # If we find 1 but not 2, maybe it's a movie or single ep.
                            # If we miss a middle one, we might stop early.
                            # For now, we assume sequential and stop on first miss to save time.
                            print(f"Stopped at episode {ep_num} (not found)")
                            break
                        
                        # Small delay between episodes of the same anime
                        await asyncio.sleep(0.2)
                    
                    # Store the result as a JSON string
                    anime['embed_url'] = json.dumps(episode_map)
                    print(f"Collected {len(episode_map)} episodes for {slug}")
                    
                    # Write immediately and flush
                    writer.writerow(anime)
                    f_out.flush()
                    
                    # Rate limiting between animes
                    await asyncio.sleep(0.5)
            
    except Exception as e:
        print(f"Error during processing: {e}")


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
