"""
Configuration settings and preferences
"""

import os
import json
from typing import Dict, Any


class Config:
    """Configuration management"""
    
    def __init__(self, config_file: str = "burpy_config.json"):
        self.config_file = config_file
        self.settings = self._default_settings()
        self.load_config()
        
    def _default_settings(self) -> Dict[str, Any]:
        """Default configuration settings"""
        return {
            'proxy': {
                'host': '127.0.0.1',
                'port': 8080,
                'enabled': True
            },
            'scanner': {
                'timeout': 10,
                'max_threads': 5,
                'follow_redirects': True
            },
            'intruder': {
                'max_threads': 10,
                'delay': 0.1
            },
            'history': {
                'max_entries': 1000,
                'auto_save': True
            },
            'output': {
                'verbose': True,
                'color': True,
                'save_reports': True
            }
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
        
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        settings = self.settings
        
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
            
        settings[keys[-1]] = value
        self.save_config()
        
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self.settings.update(loaded_config)
        except Exception as e:
            print(f"[-] Error loading config: {e}")
            
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"[-] Error saving config: {e}")
            
    def reset(self):
        """Reset to default configuration"""
        self.settings = self._default_settings()
        self.save_config()