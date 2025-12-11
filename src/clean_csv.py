import csv
import re
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, "data", "csvs", "anime_az_list.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "csvs", "clean-anime.csv")

def slug_to_title(slug):
    if not slug:
        return "Unknown"
    # Basic slug conversion: "jujutsu-kaisen-2nd-season" -> "Jujutsu Kaisen 2nd Season"
    return slug.replace("-", " ").title()

def clean_title(title, slug):
    original_title = title
    
    # Pattern 1: Suffix noise (e.g., "Maison IkkokuTV96 Eps", "TitleTV12 Eps")
    # Matches "TV", "Movie", "OVA", "ONA", "Special" followed by digits (optional) and ending with "Eps" (optional)
    # Be careful not to remove valid title parts, but these patterns seem specific to the scraper artifacts.
    # The artifact usually looks like "TV12 Eps" or "Movie1 Eps" attached to the end.
    cleaned = re.sub(r'(TV|Movie|OVA|ONA|Special)\d+(\s*Eps)?$', '', title, flags=re.IGNORECASE)
    
    # Pattern 2: Title became just the artifact (e.g., "96TV", "12OVA")
    # If the title is just digits + type, it's likely garbage.
    if re.match(r'^\d+(TV|Movie|OVA|ONA|Special)(\s*Eps)?$', cleaned, flags=re.IGNORECASE) or \
       re.match(r'^\d+(TV|Movie|OVA|ONA|Special)(\s*Eps)?$', title, flags=re.IGNORECASE):
        cleaned = "" # Force fallback
        
    cleaned = cleaned.strip()
    
    # Fallback to slug if title is empty or just digits or very short/suspicious
    if not cleaned or cleaned.isdigit() or len(cleaned) < 2:
        # print(f"Recovering title for '{original_title}' using slug '{slug}'")
        return slug_to_title(slug)
        
    return cleaned

def clean_csv():
    try:
        with open(INPUT_FILE, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            
            rows = list(reader)
            
        cleaned_rows = []
        count_modified = 0
        
        for row in rows:
            original_title = row['title']
            slug = row['slug']
            new_title = clean_title(original_title, slug)
            
            if new_title != original_title:
                # specific logging for the requested issues
                if "96TV" in original_title or "12OVA" in original_title or "TV12 Eps" in original_title:
                    print(f"Fixed: '{original_title}' -> '{new_title}'")
                count_modified += 1
                
            row['title'] = new_title
            cleaned_rows.append(row)
            
        with open(OUTPUT_FILE, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_rows)
            
        print(f"\nProcessing complete.")
        print(f"Total rows: {len(rows)}")
        print(f"Modified rows: {count_modified}")
        print(f"Saved to {OUTPUT_FILE}")
        
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    clean_csv()
