from pydantic import BaseModel


class Anime(BaseModel):
    """
    Represents the data structure of an Anime.
    """

    title: str
    rating: str
    resolution: str
    year: str
    description: str
    watch_url: str = ""  # URL to watch the anime (canonical link)
    slug: str = ""  # URL slug (e.g., "jujutsu-kaisen-2nd-season")
    embed_url: str = ""  # JSON string of episode iframes: {"1": "url1", "2": "url2"}
