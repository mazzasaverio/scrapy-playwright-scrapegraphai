# src/crawler/utils/config_utils.py

import os
from pathlib import Path
from typing import Dict, Any
import logfire

def load_crawler_config() -> Dict[str, Any]:
    """Load crawler configuration from YAML file"""
    try:
        current_dir = Path(__file__).resolve().parent
        config_path = current_dir.parent.parent.parent / "config" / "crawler_config.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found at: {config_path}")
            
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        logfire.info("Crawler configuration loaded successfully")
        return config
        
    except Exception as e:
        logfire.error(f"Failed to load crawler config: {e}")
        raise