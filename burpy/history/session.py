"""
Session management for handling cookies, tokens, and authentication state
"""

import json
import os
import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests


class SessionManager:
    """Manages HTTP sessions with cookie and token handling"""
    
    def __init__(self, session_name: str = "default"):
        self.session_name = session_name
        self.session = requests.Session()
        self.session.verify = False
        self._lock = threading.RLock()
        self._cookies: Dict[str, Dict[str, str]] = {}
        self._tokens: Dict[str, Dict[str, str]] = {}
        self._auth_headers: Dict[str, str] = {}
        self._session_data: Dict[str, Any] = {}
        self._created_at = datetime.now()
        self._last_used = datetime.now()
        
    def update_cookies(self, cookies: Dict[str, str], domain: str = "default") -> None:
        """Update cookies for a specific domain"""
        with self._lock:
            if domain not in self._cookies:
                self._cookies[domain] = {}
            self._cookies[domain].update(cookies)
            self._update_session_cookies()
            
    def get_cookies(self, domain: str = "default") -> Dict[str, str]:
        """Get cookies for a specific domain"""
        with self._lock:
            return self._cookies.get(domain, {}).copy()
            
    def set_token(self, token_name: str, token_value: str, 
                  expiry_seconds: Optional[int] = None) -> None:
        """Set a token with optional expiry"""
        with self._lock:
            token_data: Dict[str, str] = {
                'value': token_value,
                'created': datetime.now().isoformat()
            }
            if expiry_seconds:
                token_data['expires'] = (datetime.now() + timedelta(seconds=expiry_seconds)).isoformat()
            self._tokens[token_name] = token_data
            
    def get_token(self, token_name: str) -> Optional[str]:
        """Get a token value if not expired"""
        with self._lock:
            if token_name not in self._tokens:
                return None
            token_data = self._tokens[token_name]
            if 'expires' in token_data:
                expires = datetime.fromisoformat(token_data['expires'])
                if datetime.now() > expires:
                    del self._tokens[token_name]
                    return None
            return token_data.get('value', '')
            
    def set_auth_header(self, key: str, value: str) -> None:
        """Set an authentication header"""
        with self._lock:
            self._auth_headers[key] = value
            
    def get_auth_headers(self) -> Dict[str, str]:
        """Get all authentication headers"""
        with self._lock:
            return self._auth_headers.copy()
            
    def _update_session_cookies(self) -> None:
        """Sync cookies to requests session"""
        with self._lock:
            for domain, cookies in self._cookies.items():
                for name, value in cookies.items():
                    self.session.cookies.set(name, value, domain=domain if domain != "default" else None)
            
    def save_session(self, filepath: Optional[str] = None) -> bool:
        """Save session to file"""
        if filepath is None:
            filepath = f"burpy_session_{self.session_name}.json"
        with self._lock:
            data = {
                'session_name': self.session_name,
                'created_at': self._created_at.isoformat(),
                'last_used': self._last_used.isoformat(),
                'cookies': self._cookies,
                'tokens': self._tokens,
                'auth_headers': self._auth_headers,
                'session_data': self._session_data
            }
            try:
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                return True
            except Exception as e:
                print(f"[-] Error saving session: {e}")
                return False
                
    def load_session(self, filepath: str) -> bool:
        """Load session from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            with self._lock:
                self.session_name = data.get('session_name', 'default')
                self._created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
                self._last_used = datetime.fromisoformat(data.get('last_used', datetime.now().isoformat()))
                self._cookies = data.get('cookies', {})
                self._tokens = data.get('tokens', {})
                self._auth_headers = data.get('auth_headers', {})
                self._session_data = data.get('session_data', {})
                self._update_session_cookies()
            return True
        except Exception as e:
            print(f"[-] Error loading session: {e}")
            return False
            
    def make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with session cookies and auth headers"""
        self._last_used = datetime.now()
        
        headers = kwargs.get('headers', {})
        headers.update(self._auth_headers)
        kwargs['headers'] = headers
        
        return self.session.request(method, url, **kwargs)
        
    def clone_session(self, new_name: str) -> 'SessionManager':
        """Create a copy of this session"""
        new_session = SessionManager(new_name)
        with self._lock:
            new_session._cookies = {k: v.copy() for k, v in self._cookies.items()}
            new_session._tokens = self._tokens.copy()
            new_session._auth_headers = self._auth_headers.copy()
            new_session._session_data = self._session_data.copy()
            new_session._update_session_cookies()
        return new_session
        
    def clear(self) -> None:
        """Clear all session data"""
        with self._lock:
            self._cookies = {}
            self._tokens = {}
            self._auth_headers = {}
            self._session_data = {}
            self.session = requests.Session()
            self.session.verify = False


class SessionManagerCollection:
    """Collection of multiple session managers"""
    
    def __init__(self):
        self._sessions: Dict[str, SessionManager] = {}
        self._lock = threading.RLock()
        
    def create_session(self, name: str) -> SessionManager:
        """Create a new named session"""
        with self._lock:
            session = SessionManager(name)
            self._sessions[name] = session
            return session
            
    def get_session(self, name: str) -> Optional[SessionManager]:
        """Get a session by name"""
        with self._lock:
            return self._sessions.get(name)
            
    def delete_session(self, name: str) -> bool:
        """Delete a session"""
        with self._lock:
            if name in self._sessions:
                del self._sessions[name]
                return True
            return False
            
    def list_sessions(self) -> List[str]:
        """List all session names"""
        with self._lock:
            return list(self._sessions.keys())
            
    def save_all(self, directory: str = "sessions") -> None:
        """Save all sessions to directory"""
        os.makedirs(directory, exist_ok=True)
        with self._lock:
            for name, session in self._sessions.items():
                filepath = os.path.join(directory, f"{name}.json")
                session.save_session(filepath)
                
    def load_all(self, directory: str = "sessions") -> int:
        """Load all sessions from directory"""
        loaded = 0
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.endswith('.json'):
                    name = filename[:-5]
                    session = SessionManager(name)
                    if session.load_session(os.path.join(directory, filename)):
                        self._sessions[name] = session
                        loaded += 1
        return loaded