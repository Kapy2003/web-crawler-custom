import csv

from models.venue import Anime


def is_duplicate_anime(anime_title: str, seen_names: set) -> bool:
    return anime_title in seen_names


def is_complete_anime(anime: dict, required_keys: list) -> bool:
    return all(key in anime for key in required_keys)


def save_animes_to_csv(animes: list, filename: str):
    if not animes:
        print("No animes to save.")
        return

    # Use field names from the Anime model
    fieldnames = Anime.model_fields.keys()

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(animes)
    print(f"Saved {len(animes)} animes to '{filename}'.")
