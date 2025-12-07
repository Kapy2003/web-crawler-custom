import requests
from bs4 import BeautifulSoup
from utils.iframe_extractor import extract_all_iframes

# Test URL
url = "https://hianimez.live/watch/one-piece/ep-1"

try:
    print(f"Fetching {url}...")
    response = requests.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all iframes
        iframes = soup.find_all('iframe')
        print(f"\nFound {len(iframes)} iframes:")
        
        for i, iframe in enumerate(iframes, 1):
            src = iframe.get('src', 'NO SRC')
            print(f"\n{i}. src: {src}")
            print(f"   attributes: {dict(iframe.attrs)}")
        
        # Also check for video elements
        videos = soup.find_all('video')
        print(f"\n\nFound {len(videos)} video elements")
        
        # Check for script tags with src
        scripts = soup.find_all('script')
        print(f"\nFound {len(scripts)} script tags")
        
        # Look for embed patterns in the HTML
        html_text = response.text
        if 'otakuhg' in html_text:
            print("\n✓ Found 'otakuhg' in HTML - video hosting service is used")
        
        if 'src=' in html_text:
            import re
            srcs = re.findall(r'src=["\']([^"\']*)["\']', html_text)
            print(f"\nAll src attributes found ({len(srcs)} total):")
            for src in srcs[:10]:  # Show first 10
                if 'otakuhg' in src or 'iframe' in src.lower():
                    print(f"  ✓ {src}")
    else:
        print(f"Failed to fetch page: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
