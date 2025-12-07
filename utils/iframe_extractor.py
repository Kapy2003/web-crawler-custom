import re
from bs4 import BeautifulSoup
from typing import Optional


def extract_iframe_src(html_content: str) -> Optional[str]:
    """
    Extracts the iframe src attribute from HTML content.
    
    Args:
        html_content (str): The HTML content to search.
    
    Returns:
        Optional[str]: The iframe src URL if found, None otherwise.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        iframe = soup.find('iframe', {'src': re.compile(r'https://')})
        if iframe and iframe.get('src'):
            return iframe['src']
    except Exception as e:
        print(f"Error extracting iframe src: {e}")
    
    return None


def extract_all_iframes(html_content: str) -> list:
    """
    Extracts all iframe src attributes from HTML content.
    
    Args:
        html_content (str): The HTML content to search.
    
    Returns:
        list: List of iframe src URLs found.
    """
    iframes = []
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        all_iframes = soup.find_all('iframe')
        for iframe in all_iframes:
            src = iframe.get('src')
            if src:
                iframes.append(src)
    except Exception as e:
        print(f"Error extracting iframes: {e}")
    
    return iframes
