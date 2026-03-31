"""
Request/Response Editor for modifying HTTP requests interactively
"""

import json
import re
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse, urlencode, parse_qs


class RequestEditor:
    """Editor for modifying HTTP requests and responses"""
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        
    def parse_request(self, raw_request: str) -> Dict[str, Any]:
        """Parse raw HTTP request into components"""
        lines = raw_request.strip().split('\r\n')
        
        request_line = lines[0].strip().split()
        method = request_line[0]
        url = request_line[1]
        version = request_line[2] if len(request_line) > 2 else 'HTTP/1.1'
        
        headers = {}
        body_start = len(lines)
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '':
                body_start = i + 1
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
                
        body = '\r\n'.join(lines[body_start:]) if body_start < len(lines) else ''
        
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        return {
            'method': method,
            'url': url,
            'url_parsed': {
                'scheme': parsed_url.scheme,
                'netloc': parsed_url.netloc,
                'path': parsed_url.path,
                'params': parsed_url.params,
                'query': parsed_url.query,
                'query_params': query_params,
                'fragment': parsed_url.fragment
            },
            'version': version,
            'headers': headers,
            'body': body,
            'raw': raw_request
        }
        
    def build_request(self, request: Dict[str, Any]) -> str:
        """Build raw HTTP request from components"""
        lines = []
        lines.append(f"{request['method']} {request['url']} {request['version']}")
        
        for key, value in request.get('headers', {}).items():
            lines.append(f"{key}: {value}")
            
        lines.append('')
        
        body = request.get('body', '')
        if body:
            lines.append(body)
            
        return '\r\n'.join(lines)
        
    def modify_method(self, request: Dict[str, Any], new_method: str) -> Dict[str, Any]:
        """Change HTTP method"""
        new_request = request.copy()
        new_request['method'] = new_method.upper()
        new_request['raw'] = self.build_request(new_request)
        return new_request
        
    def modify_url(self, request: Dict[str, Any], new_url: str) -> Dict[str, Any]:
        """Change request URL"""
        new_request = request.copy()
        new_request['url'] = new_url
        new_request['raw'] = self.build_request(new_request)
        return new_request
        
    def modify_header(self, request: Dict[str, Any], header: str, value: str, 
                      remove: bool = False) -> Dict[str, Any]:
        """Add, modify, or remove a header"""
        new_request = request.copy()
        headers = new_request.get('headers', {}).copy()
        
        if remove:
            headers.pop(header, None)
        else:
            headers[header] = value
            
        new_request['headers'] = headers
        new_request['raw'] = self.build_request(new_request)
        return new_request
        
    def modify_body(self, request: Dict[str, Any], new_body: str, 
                   content_type: Optional[str] = None) -> Dict[str, Any]:
        """Change request body"""
        new_request = request.copy()
        new_request['body'] = new_body
        
        headers = new_request.get('headers', {}).copy()
        if content_type:
            headers['Content-Type'] = content_type
        new_request['headers'] = headers
        new_request['raw'] = self.build_request(new_request)
        return new_request
        
    def add_query_param(self, request: Dict[str, Any], key: str, value: str) -> Dict[str, Any]:
        """Add query parameter"""
        new_request = request.copy()
        parsed = new_request['url_parsed'].copy()
        
        query_params = parsed.get('query_params', {})
        query_params[key] = [value]
        
        new_query = urlencode(query_params, doseq=True)
        new_url = f"{parsed['scheme']}://{parsed['netloc']}{parsed['path']}"
        if new_query:
            new_url += f"?{new_query}"
            
        new_request['url'] = new_url
        new_request['url_parsed']['query'] = new_query
        new_request['url_parsed']['query_params'] = query_params
        new_request['raw'] = self.build_request(new_request)
        return new_request
        
    def remove_query_param(self, request: Dict[str, Any], key: str) -> Dict[str, Any]:
        """Remove query parameter"""
        new_request = request.copy()
        parsed = new_request['url_parsed'].copy()
        
        query_params = parsed.get('query_params', {})
        query_params.pop(key, None)
        
        new_query = urlencode(query_params, doseq=True)
        new_url = f"{parsed['scheme']}://{parsed['netloc']}{parsed['path']}"
        if new_query:
            new_url += f"?{new_query}"
            
        new_request['url'] = new_url
        new_request['url_parsed']['query'] = new_query
        new_request['url_parsed']['query_params'] = query_params
        new_request['raw'] = self.build_request(new_request)
        return new_request


class ResponseEditor:
    """Editor for modifying HTTP responses"""
    
    def __init__(self):
        pass
        
    def parse_response(self, raw_response: str) -> Dict[str, Any]:
        """Parse raw HTTP response"""
        lines = raw_response.strip().split('\r\n')
        
        status_line = lines[0].strip().split(None, 2)
        version = status_line[0]
        status_code = int(status_line[1])
        reason = status_line[2] if len(status_line) > 2 else ''
        
        headers = {}
        body_start = len(lines)
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '':
                body_start = i + 1
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
                
        body = '\r\n'.join(lines[body_start:]) if body_start < len(lines) else ''
        
        return {
            'version': version,
            'status_code': status_code,
            'reason': reason,
            'headers': headers,
            'body': body,
            'raw': raw_response
        }
        
    def build_response(self, response: Dict[str, Any]) -> str:
        """Build raw HTTP response"""
        lines = []
        lines.append(f"{response['version']} {response['status_code']} {response['reason']}")
        
        for key, value in response.get('headers', {}).items():
            lines.append(f"{key}: {value}")
            
        lines.append('')
        
        body = response.get('body', '')
        if body:
            lines.append(body)
            
        return '\r\n'.join(lines)
        
    def modify_status(self, response: Dict[str, Any], new_status: int, 
                     new_reason: Optional[str] = None) -> Dict[str, Any]:
        """Change response status code"""
        new_response = response.copy()
        new_response['status_code'] = new_status
        if new_reason:
            new_response['reason'] = new_reason
        new_response['raw'] = self.build_response(new_response)
        return new_response
        
    def modify_header(self, response: Dict[str, Any], header: str, value: str,
                     remove: bool = False) -> Dict[str, Any]:
        """Add, modify, or remove response header"""
        new_response = response.copy()
        headers = new_response.get('headers', {}).copy()
        
        if remove:
            headers.pop(header, None)
        else:
            headers[header] = value
            
        new_response['headers'] = headers
        new_response['raw'] = self.build_response(new_response)
        return new_response
        
    def modify_body(self, response: Dict[str, Any], new_body: str) -> Dict[str, Any]:
        """Change response body"""
        new_response = response.copy()
        new_response['body'] = new_body
        new_response['raw'] = self.build_response(new_response)
        return new_response
        
    def inject_header(self, response: Dict[str, Any], header: str, value: str) -> Dict[str, Any]:
        """Inject a security header"""
        return self.modify_header(response, header, value)


class DiffAnalyzer:
    """Analyze differences between requests/responses"""
    
    @staticmethod
    def compare_requests(req1: Dict[str, Any], req2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two requests and highlight differences"""
        diff = {
            'method_changed': req1.get('method') != req2.get('method'),
            'url_changed': req1.get('url') != req2.get('url'),
            'headers_changed': {},
            'body_changed': req1.get('body') != req2.get('body')
        }
        
        all_headers = set(req1.get('headers', {}).keys()) | set(req2.get('headers', {}).keys())
        for header in all_headers:
            val1 = req1.get('headers', {}).get(header)
            val2 = req2.get('headers', {}).get(header)
            if val1 != val2:
                diff['headers_changed'][header] = {'before': val1, 'after': val2}
                
        return diff
        
    @staticmethod
    def compare_responses(resp1: Dict[str, Any], resp2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two responses"""
        diff = {
            'status_changed': resp1.get('status_code') != resp2.get('status_code'),
            'headers_changed': {},
            'body_changed': resp1.get('body') != resp2.get('body')
        }
        
        all_headers = set(resp1.get('headers', {}).keys()) | set(resp2.get('headers', {}).keys())
        for header in all_headers:
            val1 = resp1.get('headers', {}).get(header)
            val2 = resp2.get('headers', {}).get(header)
            if val1 != val2:
                diff['headers_changed'][header] = {'before': val1, 'after': val2}
                
        return diff