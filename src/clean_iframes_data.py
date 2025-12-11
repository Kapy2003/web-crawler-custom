import csv
import json
import re
import os
import shutil

# Config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_INPUT = os.path.join(BASE_DIR, "data", "csvs", "anime_az_list_with_iframes.csv")
CSV_OUTPUT = os.path.join(BASE_DIR, "data", "csvs", "clean_anime_with_iframes.csv")
JSONL_INPUT = os.path.join(BASE_DIR, "data", "jsonls", "anime_az_list_with_iframes.jsonl")
JSONL_OUTPUT = os.path.join(BASE_DIR, "data", "jsonls", "clean_anime_with_iframes.jsonl")

def slug_to_title(slug):
    if not slug:
        return "Unknown"
    return slug.replace("-", " ").title()

def clean_title(title, slug):
    original_title = title
    
    # Pattern 1: Suffix noise
    cleaned = re.sub(r'(TV|Movie|OVA|ONA|Special)\d+(\s*Eps)?$', '', title, flags=re.IGNORECASE)
    
    # Pattern 2: Title became just the artifact
    if re.match(r'^\d+(TV|Movie|OVA|ONA|Special)(\s*Eps)?$', cleaned, flags=re.IGNORECASE) or \
       re.match(r'^\d+(TV|Movie|OVA|ONA|Special)(\s*Eps)?$', title, flags=re.IGNORECASE):
        cleaned = "" 
        
    cleaned = cleaned.strip()
    
    if not cleaned or cleaned.isdigit() or len(cleaned) < 2:
        return slug_to_title(slug)
        
    return cleaned

def clean_iframes_files():
    # 1. Process CSV
    if os.path.exists(CSV_INPUT):
        print(f"Processing {CSV_INPUT}...")
        try:
            with open(CSV_INPUT, 'r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames
                rows = list(reader)
            
            cleaned_count = 0
            for row in rows:
                original = row.get('title', '')
                slug = row.get('slug', '')
                new_title = clean_title(original, slug)
                if new_title != original:
                    cleaned_count += 1
                row['title'] = new_title
                
            with open(CSV_OUTPUT, 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
                
            print(f" - Saved {CSV_OUTPUT} (Fixed {cleaned_count} titles)")
        except Exception as e:
            print(f"Error processing CSV: {e}")
    else:
        print(f"Skipping CSV (not found): {CSV_INPUT}")

    # 2. Process JSONL
    if os.path.exists(JSONL_INPUT):
        print(f"Processing {JSONL_INPUT}...")
        try:
            updated_lines = []
            cleaned_count = 0
            
            with open(JSONL_INPUT, 'r', encoding='utf-8') as infile:
                for line in infile:
                    line = line.strip()
                    if not line: continue
                    
                    try:
                        data = json.loads(line)
                        original = data.get('title', '')
                        slug = data.get('slug', '')
                        new_title = clean_title(original, slug)
                        
                        if new_title != original:
                            cleaned_count += 1
                        
                        data['title'] = new_title
                        updated_lines.append(json.dumps(data))
                    except json.JSONDecodeError:
                        print(f"Skipping invalid JSON line")
                        continue
                        
            with open(JSONL_OUTPUT, 'w', encoding='utf-8') as outfile:
                for line in updated_lines:
                    outfile.write(line + '\n')
            
            print(f" - Saved {JSONL_OUTPUT} (Fixed {cleaned_count} titles)")
            
        except Exception as e:
            print(f"Error processing JSONL: {e}")
    else:
        print(f"Skipping JSONL (not found): {JSONL_INPUT}")

if __name__ == "__main__":
    clean_iframes_files()
