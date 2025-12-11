import csv
import json
import asyncio
import os
from typing import List, Set, Dict, Any
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from utils.iframe_extractor import extract_iframe_src
from dotenv import load_dotenv

load_dotenv()

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
    # Base URL for watching episodes, e.g., "https://example.com/watch"
    watch_base = os.getenv("WATCH_BASE_URL", "https://example.com/watch")
    url = f"{watch_base}/{anime_slug}/ep-{episode_num}"
    
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
                pass
        else:
            print(f"✗ Failed to fetch {url}: {result.error_message}")
    except Exception as e:
        print(f"✗ Error fetching {url}: {e}")
    
    return ""


async def enrich_anime_with_iframes(
    csv_input_file: str,
    csv_output_file: str = None, 
    json_output_file: str = None,
    max_episodes: int = 10000,
) -> None:
    """
    Reads anime from CSV and fetches iframe URLs for episodes.
    
    Args:
        csv_input_file (str): Path to input CSV file.
        csv_output_file (str): Path to output CSV file with embed_url column.
        json_output_file (str): Path to output JSONL file (incremental).
        max_episodes (int): Maximum number of episodes to attempt (for pagination).
    """
    if not csv_output_file and not json_output_file:
        print("Error: Must provide either csv_output_file or json_output_file")
        return

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        verbose=False,
    )
    
    animes = []
    
    # Read input CSV
    try:
        if not os.path.exists(csv_input_file):
            print(f"Input file not found: {csv_input_file}")
            return
            
        with open(csv_input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            animes = list(reader)
        print(f"Loaded {len(animes)} anime from {csv_input_file}")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    
    # Check for existing progress
    processed_slugs = set()
    
    # helper to load from jsonl
    json_slugs = set()
    if json_output_file and os.path.exists(json_output_file):
        try:
            valid_lines = []
            needs_repair = False
            
            with open(json_output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Naive repair for the specific "}{" issue reported
            if '}{' in content:
                print("Detected corrupted JSONL (missing newlines). Repairing...")
                content = content.replace('}{', '}\n{')
                needs_repair = True
            
            # Re-read lines from the (potentially repaired) content
            import io
            f_io = io.StringIO(content)
            
            for line in f_io:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get('slug'):
                        json_slugs.add(data['slug'])
                    valid_lines.append(line)
                except json.JSONDecodeError:
                    print(f"Skipping invalid JSON line during load: {line[:50]}...")
                    needs_repair = True
            
            print(f"JSONL: Found {len(valid_lines)} valid processed animes.")
            
            # Rewrite file if repair was needed to ensure cleanliness
            if needs_repair:
                print("Rewriting repaired JSONL file...")
                with open(json_output_file, 'w', encoding='utf-8') as f:
                    for line in valid_lines:
                        f.write(line + '\n')
                        
        except Exception as e:
            print(f"Error reading/repairing existing parsed JSONL file: {e}")

    # helper to load from csv if jsonl check didn't cover it or wasn't used
    # AND BACKFILL JSONL IF NEEDED
    if csv_output_file and os.path.exists(csv_output_file):
        try:
            csv_rows_to_backfill = []
            with open(csv_output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    slug = row.get('slug')
                    if slug:
                        processed_slugs.add(slug)
                        if json_output_file and slug not in json_slugs:
                             csv_rows_to_backfill.append(row)
            
            print(f"CSV: Found {len(processed_slugs)} processed animes.")
            
            # Backfill step
            if csv_rows_to_backfill and json_output_file:
                print(f"Backfilling {len(csv_rows_to_backfill)} items from CSV to JSONL...")
                with open(json_output_file, 'a', encoding='utf-8') as f_json:
                    for row in csv_rows_to_backfill:
                        record = row.copy()
                        try:
                            # Try to parse the nested JSON string if it exists
                            if isinstance(record.get('embed_url'), str):
                                record['embed_url'] = json.loads(record['embed_url'])
                        except:
                            # If it fails or isn't there, keep as is
                            pass
                        json.dump(record, f_json)
                        f_json.write('\n')
                print("Backfill complete.")
                # Update json_slugs
                for row in csv_rows_to_backfill:
                    json_slugs.add(row['slug'])

        except Exception as e:
            print(f"Error reading existing output CSV file: {e}")
            return
    
    # Combined processed slugs
    processed_slugs.update(json_slugs)
    print(f"Total processed slugs (after sync): {len(processed_slugs)}")

    # Open CSV writer if needed
    csv_f = None
    csv_writer = None
    
    if csv_output_file:
        file_exists = os.path.exists(csv_output_file)
        csv_f = open(csv_output_file, 'a', newline='', encoding='utf-8')
        fieldnames = list(animes[0].keys()) if animes else []
        if 'embed_url' not in fieldnames:
            fieldnames.append('embed_url')
        csv_writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
        if not file_exists and fieldnames:
            csv_writer.writeheader()

    # Open JSONL writer if needed
    jsonl_f = None
    if json_output_file:
        jsonl_f = open(json_output_file, 'a', encoding='utf-8')

    try:
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
                        print(f"Stopped at episode {ep_num} (not found)")
                        break
                    
                    # Small delay between episodes of the same anime
                    await asyncio.sleep(0.2)
                
                # Store data
                anime['embed_url'] = json.dumps(episode_map)
                print(f"Collected {len(episode_map)} episodes for {slug}")
                
                # Write to CSV
                if csv_writer:
                    csv_writer.writerow(anime)
                    csv_f.flush()

                # Write to JSONL
                if jsonl_f:
                    # Create a clean record for JSONL
                    record = anime.copy()
                    # Keep embed_url as plain object in JSONL for better readability
                    try:
                         record['embed_url'] = json.loads(record['embed_url'])
                    except:
                        pass
                        
                    json.dump(record, jsonl_f)
                    jsonl_f.write('\n')
                    jsonl_f.flush()
                
                # Rate limiting between animes
                await asyncio.sleep(0.5)
            
    except Exception as e:
        print(f"Error during processing: {e}")
    finally:
        if csv_f:
            csv_f.close()
        if jsonl_f:
            jsonl_f.close()


async def main():
    """
    Main function to enrich anime data with iframe URLs.
    """
    # Robust path resolution
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    await enrich_anime_with_iframes(
        csv_input_file=os.path.join(base_dir, "data", "csvs", "anime_az_list.csv"),
        csv_output_file=os.path.join(base_dir, "data", "csvs", "anime_az_list_with_iframes.csv"),
        json_output_file=os.path.join(base_dir, "data", "jsonls", "anime_az_list_with_iframes.jsonl")
    )


if __name__ == "__main__":
    asyncio.run(main())
