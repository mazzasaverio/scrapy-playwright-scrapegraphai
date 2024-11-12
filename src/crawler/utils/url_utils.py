
import re
from typing import List, Optional
from urllib.parse import urlparse, urljoin

def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def matches_pattern(url: str, patterns: List[str]) -> bool:
    """Check if URL matches any of the given patterns"""
    if not patterns:
        return False
    return any(re.search(pattern, url) for pattern in patterns)

def get_url_type_config(url: str, category_config: dict) -> Optional[dict]:
    """Get URL type configuration for given URL"""
    for url_config in category_config.get('urls', []):
        if url == url_config['url']:
            return url_config
    return None