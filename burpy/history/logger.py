"""
Request/response history logging and storage
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import os


class HistoryLogger:
    """Logger for request/response history"""
    
    def __init__(self, log_file: str = "burpy_history.json"):
        self.log_file = log_file
        self.history = []
        self.load_history()
        
    def log_request(self, request: Dict[str, Any], response: Dict[str, Any] = None):
        """Log a request and optional response"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'request': request,
            'response': response,
            'id': len(self.history) + 1
        }
        
        self.history.append(entry)
        self.save_history()
        
    def get_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get request history"""
        if limit:
            return self.history[-limit:]
        return self.history
        
    def get_request(self, request_id: int) -> Optional[Dict[str, Any]]:
        """Get specific request by ID"""
        for entry in self.history:
            if entry['id'] == request_id:
                return entry
        return None
        
    def search_history(self, query: str) -> List[Dict[str, Any]]:
        """Search history by URL, method, or content"""
        results = []
        query_lower = query.lower()
        
        for entry in self.history:
            request = entry.get('request', {})
            if (query_lower in request.get('url', '').lower() or
                query_lower in request.get('method', '').lower() or
                query_lower in request.get('body', '').lower()):
                results.append(entry)
                
        return results
        
    def save_history(self):
        """Save history to file"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"[-] Error saving history: {e}")
            
    def load_history(self):
        """Load history from file"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"[-] Error loading history: {e}")
            self.history = []
            
    def clear_history(self):
        """Clear all history"""
        self.history = []
        self.save_history()
        
    def export_history(self, filename: str):
        """Export history to a file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.history, f, indent=2)
            print(f"[+] History exported to {filename}")
        except Exception as e:
            print(f"[-] Error exporting history: {e}")