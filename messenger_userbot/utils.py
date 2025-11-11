"""
Utility functions for the messenger_userbot package
"""
import json
import os


def load_config(config_path="config.json", default_config=None):
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to config file
        default_config: Default configuration dict to use if file doesn't exist
        
    Returns:
        Configuration dictionary
    """
    if os.path.exists(config_path):
        try:
            config = json.load(open(config_path, "r"))
            if not isinstance(config, dict):
                print("Config file is not a valid JSON object")
                return default_config or {}
            return config
        except ValueError:
            print("Error parsing config file")
            return default_config or {}
    else:
        if default_config:
            json.dump(default_config, open(config_path, "w"), indent=2)
            print(f"Created default config at {config_path}")
        return default_config or {}


def save_config(config, config_path="config.json"):
    """
    Save configuration to a JSON file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save config file
    """
    json.dump(config, open(config_path, "w"), indent=2)


def cache_data(cache_id, data=None, default=None, cache_file=".cache.json"):
    """
    Simple cache system for storing data.
    
    Args:
        cache_id: Identifier for the cached data
        data: Data to cache (if None, retrieves from cache)
        default: Default value if cache doesn't exist
        cache_file: Path to cache file
        
    Returns:
        Cached data or default if retrieving
    """
    if os.path.exists(cache_file):
        cachef = json.load(open(cache_file, "r"))
    else:
        cachef = {}
    
    if data is not None:
        cachef[cache_id] = data
        json.dump(cachef, open(cache_file, "w"))
        return data
    else:
        return cachef.get(cache_id, default)
