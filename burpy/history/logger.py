"""
Request/response history logging and storage
"""

import json
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
import os


class HistoryLogger:
    """Logger for request/response history with thread safety"""
    
    def __init__(self, log_file: str = "burpy_history.json", use_sqlite: bool = False):
        self.log_file = log_file
        self.use_sqlite = use_sqlite
        self._db_path: Optional[str] = None
        self._lock = threading.RLock()
        self.history: List[Dict[str, Any]] = []
        if use_sqlite:
            self._init_sqlite()
        else:
            self.load_history()
        
    def _init_sqlite(self) -> None:
        """Initialize SQLite database for better performance"""
        db_file = self.log_file.replace('.json', '.db')
        self._db_path = db_file
        conn = sqlite3.connect(db_file, check_same_thread=False)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                method TEXT,
                url TEXT,
                headers TEXT,
                body TEXT,
                response_status INTEGER,
                response_body TEXT,
                request_raw TEXT,
                response_raw TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
    def _save_to_sqlite(self, entry: Dict[str, Any]) -> None:
        """Save entry to SQLite database"""
        if not self._db_path:
            return
        try:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            request = entry.get('request', {})
            response = entry.get('response', {})
            
            conn.execute('''
                INSERT INTO history (timestamp, method, url, headers, body,
                    response_status, response_body, request_raw, response_raw)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry['timestamp'],
                request.get('method', ''),
                request.get('url', ''),
                json.dumps(request.get('headers', {})),
                request.get('body', ''),
                response.get('status_code') if response else -1,
                response.get('content', '') if response else '',
                request.get('raw', ''),
                response.get('raw', '') if response else ''
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[-] Error saving to SQLite: {e}")
        
    def log_request(self, request: Dict[str, Any], response: Optional[Dict[str, Any]] = None):
        """Log a request and optional response (thread-safe)"""
        with self._lock:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'request': request,
                'response': response,
                'id': len(self.history) + 1
            }
            
            self.history.append(entry)
            
            if self.use_sqlite and self._db_path:
                self._save_to_sqlite(entry)
            else:
                self.save_history()
        
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get request history"""
        with self._lock:
            if limit:
                return self.history[-limit:]
            return self.history
        
    def get_request(self, request_id: int) -> Optional[Dict[str, Any]]:
        """Get specific request by ID"""
        with self._lock:
            for entry in self.history:
                if entry['id'] == request_id:
                    return entry
            return None
        
    def search_history(self, query: str) -> List[Dict[str, Any]]:
        """Search history by URL, method, or content"""
        with self._lock:
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
        with self._lock:
            try:
                with open(self.log_file, 'w') as f:
                    json.dump(self.history, f, indent=2)
            except Exception as e:
                print(f"[-] Error saving history: {e}")
                
    def load_history(self):
        """Load history from file"""
        with self._lock:
            try:
                if os.path.exists(self.log_file):
                    with open(self.log_file, 'r') as f:
                        self.history = json.load(f)
            except Exception as e:
                print(f"[-] Error loading history: {e}")
                self.history = []
            
    def clear_history(self):
        """Clear all history"""
        with self._lock:
            self.history = []
            if self.use_sqlite and self._db_path:
                try:
                    conn = sqlite3.connect(self._db_path, check_same_thread=False)
                    conn.execute("DELETE FROM history")
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"[-] Error clearing SQLite: {e}")
            else:
                self.save_history()
        
    def export_history(self, filename: str):
        """Export history to a file"""
        with self._lock:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.history, f, indent=2)
                print(f"[+] History exported to {filename}")
            except Exception as e:
                print(f"[-] Error exporting history: {e}")
                
    def export_har(self, filename: str) -> bool:
        """Export history to HAR format"""
        with self._lock:
            try:
                har_data = {
                    "log": {
                        "version": "1.2",
                        "creator": {"name": "Burpy", "version": "1.0.0"},
                        "entries": []
                    }
                }
                for entry in self.history:
                    request = entry.get('request', {})
                    response = entry.get('response', {})
                    har_entry = {
                        "startedDateTime": entry.get('timestamp', ''),
                        "request": {
                            "method": request.get('method', 'GET'),
                            "url": request.get('url', ''),
                            "httpVersion": request.get('version', 'HTTP/1.1'),
                            "headers": [
                                {"name": k, "value": v} 
                                for k, v in request.get('headers', {}).items()
                            ],
                            "queryString": [],
                            "bodySize": len(request.get('body', '')),
                            "postData": {
                                "mimeType": request.get('headers', {}).get('Content-Type', ''),
                                "text": request.get('body', '')
                            } if request.get('body') else {}
                        },
                        "response": {
                            "status": response.get('status_code', 0) if response else 0,
                            "statusText": response.get('reason', '') if response else '',
                            "httpVersion": request.get('version', 'HTTP/1.1'),
                            "headers": [
                                {"name": k, "value": v}
                                for k, v in response.get('headers', {}).items()
                            ] if response else [],
                            "bodySize": len(response.get('content', '')) if response else 0
                        },
                        "time": response.get('elapsed_time', 0) * 1000 if response else 0
                    }
                    har_data["log"]["entries"].append(har_entry)
                
                with open(filename, 'w') as f:
                    json.dump(har_data, f, indent=2)
                print(f"[+] History exported to HAR format: {filename}")
                return True
            except Exception as e:
                print(f"[-] Error exporting HAR: {e}")
                return False