
import re
from typing import List, Optional
from urllib.parse import urlparse
def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def matches_pattern(url: str, patterns: List[str]) -> bool:
    """Check if URL matches any of the given patterns with improved PDF detection"""
    if not patterns:
        return False
        
    # First do a simple check for PDF in URL (case insensitive)
    if any(pattern.lower() in url.lower() for pattern in patterns if isinstance(pattern, str)):
        return True
        
    # Then try regex patterns
    return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)

def get_url_type_config(url: str, category_config: dict) -> Optional[dict]:
    """Get URL type configuration for given URL"""
    for url_config in category_config.get('urls', []):
        if url == url_config['url']:
            return url_config
    return None