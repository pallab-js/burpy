"""
Tests for request repeater functionality
"""

import pytest
from unittest.mock import Mock, patch
from burpy.tools.repeater import RequestRepeater


class TestRequestRepeater:
    """Test cases for RequestRepeater class"""
    
    def test_repeater_initialization(self):
        """Test repeater initialization"""
        repeater = RequestRepeater()
        assert repeater.session is not None
        assert repeater.session.verify is False
    
    @patch('requests.Session.request')
    def test_send_request_success(self, mock_request):
        """Test successful request sending"""
        repeater = RequestRepeater()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = "Test response"
        mock_response.url = "https://example.com/test"
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_request.return_value = mock_response
        
        result = repeater.send_request("GET", "https://example.com/test")
        
        assert result['success'] is True
        assert result['status_code'] == 200
        assert result['headers'] == {"Content-Type": "text/html"}
        assert result['content'] == "Test response"
        assert result['url'] == "https://example.com/test"
        assert result['elapsed_time'] == 0.5
    
    @patch('requests.Session.request')
    def test_send_request_with_headers(self, mock_request):
        """Test request sending with custom headers"""
        repeater = RequestRepeater()
        
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"Location": "https://example.com/new"}
        mock_response.text = "Created"
        mock_response.url = "https://example.com/test"
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_request.return_value = mock_response
        
        headers = {"Authorization": "Bearer token123"}
        result = repeater.send_request("POST", "https://example.com/test", headers=headers)
        
        assert result['success'] is True
        assert result['status_code'] == 201
        mock_request.assert_called_once_with(
            method="POST",
            url="https://example.com/test",
            headers=headers,
            data=None,
            params=None,
            timeout=30
        )
    
    @patch('requests.Session.request')
    def test_send_request_with_data(self, mock_request):
        """Test request sending with data"""
        repeater = RequestRepeater()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = "Success"
        mock_response.url = "https://example.com/test"
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_request.return_value = mock_response
        
        data = '{"key": "value"}'
        result = repeater.send_request("POST", "https://example.com/test", data=data)
        
        assert result['success'] is True
        mock_request.assert_called_once_with(
            method="POST",
            url="https://example.com/test",
            headers={},
            data=data,
            params=None,
            timeout=30
        )
    
    @patch('requests.Session.request')
    def test_send_request_with_params(self, mock_request):
        """Test request sending with parameters"""
        repeater = RequestRepeater()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = "Success"
        mock_response.url = "https://example.com/test?q=test"
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_request.return_value = mock_response
        
        params = {"q": "test", "page": "1"}
        result = repeater.send_request("GET", "https://example.com/test", params=params)
        
        assert result['success'] is True
        mock_request.assert_called_once_with(
            method="GET",
            url="https://example.com/test",
            headers={},
            data=None,
            params=params,
            timeout=30
        )
    
    @patch('requests.Session.request')
    def test_send_request_error(self, mock_request):
        """Test request sending with error"""
        repeater = RequestRepeater()
        mock_request.side_effect = Exception("Connection error")
        
        result = repeater.send_request("GET", "https://example.com/test")
        
        assert result['success'] is False
        assert 'error' in result
        assert result['error'] == "Connection error"
        assert result['url'] == "https://example.com/test"
    
    def test_parse_http_request_valid(self):
        """Test parsing valid HTTP request"""
        repeater = RequestRepeater()
        
        raw_request = """GET /api/users HTTP/1.1
Host: example.com
Authorization: Bearer token123
Content-Type: application/json

{"query": "test"}"""
        
        result = repeater.parse_http_request(raw_request)
        
        assert result['method'] == 'GET'
        assert result['url'] == '/api/users'
        assert result['version'] == 'HTTP/1.1'
        assert result['headers']['Host'] == 'example.com'
        assert result['headers']['Authorization'] == 'Bearer token123'
        assert result['headers']['Content-Type'] == 'application/json'
        assert result['body'] == '{"query": "test"}'
    
    def test_parse_http_request_minimal(self):
        """Test parsing minimal HTTP request"""
        repeater = RequestRepeater()
        
        raw_request = "GET / HTTP/1.1\r\n\r\n"
        
        result = repeater.parse_http_request(raw_request)
        
        assert result['method'] == 'GET'
        assert result['url'] == '/'
        assert result['version'] == 'HTTP/1.1'
        assert result['headers'] == {}
        assert result['body'] == ''
    
    def test_parse_http_request_with_headers_no_body(self):
        """Test parsing request with headers but no body"""
        repeater = RequestRepeater()
        
        raw_request = """POST /api/data HTTP/1.1\r\nHost: example.com\r\nContent-Type: application/json\r\nContent-Length: 0\r\n\r\n"""
        
        result = repeater.parse_http_request(raw_request)
        
        assert result['method'] == 'POST'
        assert result['url'] == '/api/data'
        assert result['headers']['Host'] == 'example.com'
        assert result['headers']['Content-Type'] == 'application/json'
        assert result['body'] == ''
    
    def test_parse_http_request_multiline_body(self):
        """Test parsing request with multiline body"""
        repeater = RequestRepeater()
        
        raw_request = """POST /api/data HTTP/1.1
Host: example.com
Content-Type: application/json

{
  "name": "test",
  "value": "data"
}"""
        
        result = repeater.parse_http_request(raw_request)
        
        assert result['method'] == 'POST'
        assert result['body'] == '{\n  "name": "test",\n  "value": "data"\n}'
    
    def test_format_response_success(self):
        """Test formatting successful response"""
        repeater = RequestRepeater()
        
        response = {
            'success': True,
            'status_code': 200,
            'headers': {'Content-Type': 'text/html', 'Server': 'nginx'},
            'content': 'Hello World',
            'url': 'https://example.com/test',
            'elapsed_time': 0.5
        }
        
        formatted = repeater.format_response(response)
        
        assert 'Status: 200' in formatted
        assert 'URL: https://example.com/test' in formatted
        assert 'Time: 0.50s' in formatted
        assert 'Headers:' in formatted
        assert 'Content-Type: text/html' in formatted
        assert 'Server: nginx' in formatted
        assert 'Body:' in formatted
        assert 'Hello World' in formatted
    
    def test_format_response_error(self):
        """Test formatting error response"""
        repeater = RequestRepeater()
        
        response = {
            'success': False,
            'error': 'Connection timeout'
        }
        
        formatted = repeater.format_response(response)
        
        assert formatted == 'Error: Connection timeout'
    
    def test_format_response_detailed(self):
        """Test formatting response with detailed information"""
        repeater = RequestRepeater()
        
        response = {
            'success': True,
            'status_code': 404,
            'headers': {
                'Content-Type': 'application/json',
                'X-Custom-Header': 'test-value'
            },
            'content': '{"error": "Not found"}',
            'url': 'https://api.example.com/users/999',
            'elapsed_time': 1.25
        }
        
        formatted = repeater.format_response(response)
        
        assert 'Status: 404' in formatted
        assert 'URL: https://api.example.com/users/999' in formatted
        assert 'Time: 1.25s' in formatted
        assert 'X-Custom-Header: test-value' in formatted
        assert '{"error": "Not found"}' in formatted
    
    @patch('requests.Session.request')
    def test_send_request_timeout(self, mock_request):
        """Test request sending with timeout"""
        repeater = RequestRepeater()
        mock_request.side_effect = Exception("Request timeout")
        
        result = repeater.send_request("GET", "https://example.com/test")
        
        assert result['success'] is False
        assert 'timeout' in result['error'].lower()
    
    @patch('requests.Session.request')
    def test_send_request_redirect(self, mock_request):
        """Test request sending with redirect"""
        repeater = RequestRepeater()
        
        mock_response = Mock()
        mock_response.status_code = 301
        mock_response.headers = {"Location": "https://example.com/new"}
        mock_response.text = "Moved"
        mock_response.url = "https://example.com/redirect"
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_request.return_value = mock_response
        
        result = repeater.send_request("GET", "https://example.com/old")
        
        assert result['success'] is True
        assert result['status_code'] == 301
        assert result['url'] == "https://example.com/redirect"