# config.py

BASE_URL = "https://hianimez.live/az-list/all"
CSS_SELECTOR = "div[class*='item'], article, section[class*='anime']"  # Adjust based on actual structure
CANONICAL_SELECTOR = "link[rel='canonical']"  # Select canonical link
REQUIRED_KEYS = [
    "title",
    "slug",
]
# Optional keys that enhance the data but aren't required
OPTIONAL_KEYS = [
    "rating",
    "resolution",
    "year",
    "description",
    "watch_url",
]
