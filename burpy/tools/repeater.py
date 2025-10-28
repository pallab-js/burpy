"""
Request repeater tool for manual testing
"""

import requests
import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse


class RequestRepeater:
    """Tool for repeating and modifying HTTP requests"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        
    def send_request(self, method: str, url: str, headers: Dict[str, str] = None, 
                    data: str = None, params: Dict[str, str] = None) -> Dict[str, Any]:
        """Send an HTTP request and return response details"""
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers or {},
                data=data,
                params=params,
                timeout=30
            )
            
            return {
                'success': True,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'url': response.url,
                'elapsed_time': response.elapsed.total_seconds()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
            
    def parse_http_request(self, raw_request: str) -> Dict[str, Any]:
        """Parse raw HTTP request string"""
        lines = raw_request.strip().split('\r\n')
        
        # Parse request line
        request_line = lines[0].strip().split()
        method = request_line[0]
        url = request_line[1]
        version = request_line[2] if len(request_line) > 2 else 'HTTP/1.1'
        
        # Parse headers
        headers = {}
        body_start = len(lines)  # Default to end if no empty line found
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '':
                body_start = i + 1
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
                
        # Parse body
        body = '\r\n'.join(lines[body_start:]) if body_start < len(lines) else ''
        
        return {
            'method': method,
            'url': url,
            'version': version,
            'headers': headers,
            'body': body
        }
        
    def format_response(self, response: Dict[str, Any]) -> str:
        """Format response for display"""
        if not response['success']:
            return f"Error: {response['error']}"
            
        output = []
        output.append(f"Status: {response['status_code']}")
        output.append(f"URL: {response['url']}")
        output.append(f"Time: {response['elapsed_time']:.2f}s")
        output.append("")
        output.append("Headers:")
        for key, value in response['headers'].items():
            output.append(f"  {key}: {value}")
        output.append("")
        output.append("Body:")
        output.append(response['content'])
        
        return '\n'.join(output)