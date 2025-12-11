import csv
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_INPUT = os.path.join(BASE_DIR, "data", "csvs", "anime_az_list_with_iframes.csv")
JSONL_OUTPUT = os.path.join(BASE_DIR, "data", "jsonls", "test.jsonl")

def sync_csv_to_jsonl():
    # 1. Load existing slugs from JSONL to avoid duplicates
    existing_slugs = set()
    if os.path.exists(JSONL_OUTPUT):
        print(f"Reading existing JSONL: {JSONL_OUTPUT}")
        try:
            with open(JSONL_OUTPUT, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        data = json.loads(line)
                        if 'slug' in data:
                            existing_slugs.add(data['slug'])
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading JSONL: {e}")
    
    print(f"Found {len(existing_slugs)} existing items in JSONL.")

    # 2. Read CSV and append new items
    if not os.path.exists(CSV_INPUT):
        print(f"CSV not found: {CSV_INPUT}")
        return

    new_items_count = 0
    print(f"Reading CSV: {CSV_INPUT}")
    
    try:
        with open(CSV_INPUT, 'r', encoding='utf-8') as csv_f, \
             open(JSONL_OUTPUT, 'a', encoding='utf-8') as jsonl_f:
            
            reader = csv.DictReader(csv_f)
            
            for row in reader:
                slug = row.get('slug')
                
                # The Twist: Skip if exactly this anime is already in JSONL
                if slug in existing_slugs:
                    continue
                
                # Prepare data for JSONL
                # We need to ensure 'embed_url' is a proper list/dict, not a string
                record = row.copy()
                if 'embed_url' in record and isinstance(record['embed_url'], str):
                    try:
                        # Try to unwrap the double-encoded string if it exists
                        # CSV usually stores complex objects as strings
                        record['embed_url'] = json.loads(record['embed_url'])
                    except:
                        pass # Leave as string if it fails
                
                # Write to JSONL
                json.dump(record, jsonl_f)
                jsonl_f.write('\n')
                
                existing_slugs.add(slug) # Add to set to prevent dupes within the CSV itself
                new_items_count += 1
                
        print(f"Sync complete. Added {new_items_count} new items to JSONL.")

    except Exception as e:
        print(f"Error during sync: {e}")

if __name__ == "__main__":
    sync_csv_to_jsonl()
