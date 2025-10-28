"""
Tests for HTTP proxy functionality
"""

import pytest
import socket
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from burpy.core.proxy import HTTPProxy


class TestHTTPProxy:
    """Test cases for HTTPProxy class"""
    
    def test_proxy_initialization(self):
        """Test proxy initialization"""
        proxy = HTTPProxy("127.0.0.1", 8080)
        assert proxy.host == "127.0.0.1"
        assert proxy.port == 8080
        assert proxy.running is False
        assert proxy.server_socket is None
        assert len(proxy.request_handlers) == 0
        assert len(proxy.response_handlers) == 0
    
    def test_add_request_handler(self):
        """Test adding request handlers"""
        proxy = HTTPProxy()
        handler = Mock()
        proxy.add_request_handler(handler)
        assert handler in proxy.request_handlers
    
    def test_add_response_handler(self):
        """Test adding response handlers"""
        proxy = HTTPProxy()
        handler = Mock()
        proxy.add_response_handler(handler)
        assert handler in proxy.response_handlers
    
    def test_parse_request_valid(self):
        """Test parsing valid HTTP request"""
        proxy = HTTPProxy()
        request_data = "GET /test HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Test\r\n\r\nbody data"
        
        result = proxy._parse_request(request_data)
        
        assert result is not None
        assert result['method'] == 'GET'
        assert result['url'] == '/test'
        assert result['version'] == 'HTTP/1.1'
        assert result['headers']['Host'] == 'example.com'
        assert result['headers']['User-Agent'] == 'Test'
        assert result['body'] == 'body data'
    
    def test_parse_request_invalid(self):
        """Test parsing invalid HTTP request"""
        proxy = HTTPProxy()
        
        # Empty request
        assert proxy._parse_request("") is None
        
        # Malformed request line
        assert proxy._parse_request("GET") is None
        
        # Invalid format
        assert proxy._parse_request("INVALID REQUEST") is None
    
    def test_parse_request_with_body(self):
        """Test parsing request with body"""
        proxy = HTTPProxy()
        request_data = """POST /api/test HTTP/1.1\r\nHost: example.com\r\nContent-Type: application/json\r\nContent-Length: 20\r\n\r\n{"key": "value"}"""
        
        result = proxy._parse_request(request_data)
        
        assert result is not None
        assert result['method'] == 'POST'
        assert result['body'] == '{"key": "value"}'
        assert result['headers']['Content-Type'] == 'application/json'
    
    @patch('requests.request')
    def test_forward_request_success(self, mock_request):
        """Test successful request forwarding"""
        proxy = HTTPProxy()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = "Response content"
        mock_request.return_value = mock_response
        
        request = {
            'method': 'GET',
            'url': 'https://example.com/test',
            'version': 'HTTP/1.1',
            'headers': {'Host': 'example.com'},
            'body': ''
        }
        
        result = proxy._forward_request(request)
        
        assert result is not None
        assert "200 OK" in result
        assert "Response content" in result
        mock_request.assert_called_once()
    
    @patch('requests.request')
    def test_forward_request_with_body(self, mock_request):
        """Test request forwarding with body"""
        proxy = HTTPProxy()
        
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.reason = "Created"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"status": "created"}'
        mock_request.return_value = mock_response
        
        request = {
            'method': 'POST',
            'url': 'https://example.com/api',
            'version': 'HTTP/1.1',
            'headers': {'Content-Type': 'application/json'},
            'body': '{"data": "test"}'
        }
        
        result = proxy._forward_request(request)
        
        assert result is not None
        assert "201 Created" in result
        assert '{"status": "created"}' in result
        mock_request.assert_called_once_with(
            method='POST',
            url='https://example.com/api',
            headers={'Content-Type': 'application/json'},
            data='{"data": "test"}',
            allow_redirects=False,
            verify=False,
            timeout=30
        )
    
    @patch('requests.request')
    def test_forward_request_error(self, mock_request):
        """Test request forwarding with error"""
        proxy = HTTPProxy()
        mock_request.side_effect = Exception("Connection error")
        
        request = {
            'method': 'GET',
            'url': 'https://example.com/test',
            'version': 'HTTP/1.1',
            'headers': {},
            'body': ''
        }
        
        result = proxy._forward_request(request)
        assert result is None
    
    def test_handle_client_with_request_handlers(self):
        """Test client handling with request handlers"""
        proxy = HTTPProxy()
        
        # Mock socket
        mock_socket = Mock()
        mock_socket.recv.return_value = b"GET /test HTTP/1.1\r\nHost: example.com\r\n\r\n"
        mock_socket.send.return_value = None
        
        # Add request handler
        request_handler = Mock()
        request_handler.return_value = None  # Handler doesn't modify request
        proxy.add_request_handler(request_handler)
        
        # Add response handler
        response_handler = Mock()
        response_handler.return_value = "HTTP/1.1 200 OK\r\n\r\nTest response"
        proxy.add_response_handler(response_handler)
        
        with patch.object(proxy, '_forward_request', return_value="HTTP/1.1 200 OK\r\n\r\nTest response"):
            proxy._handle_client(mock_socket, ("127.0.0.1", 12345))
        
        # Verify handlers were called
        request_handler.assert_called_once()
        response_handler.assert_called_once()
        mock_socket.send.assert_called_once()
    
    def test_handle_client_empty_request(self):
        """Test client handling with empty request"""
        proxy = HTTPProxy()
        
        mock_socket = Mock()
        mock_socket.recv.return_value = b""
        
        proxy._handle_client(mock_socket, ("127.0.0.1", 12345))
        
        # Should not crash and should close socket
        mock_socket.close.assert_called_once()
    
    def test_handle_client_parse_error(self):
        """Test client handling with parse error"""
        proxy = HTTPProxy()
        
        mock_socket = Mock()
        mock_socket.recv.return_value = b"INVALID REQUEST DATA"
        
        proxy._handle_client(mock_socket, ("127.0.0.1", 12345))
        
        # Should not crash and should close socket
        mock_socket.close.assert_called_once()
    
    def test_handle_client_exception(self):
        """Test client handling with exception"""
        proxy = HTTPProxy()
        
        mock_socket = Mock()
        mock_socket.recv.side_effect = Exception("Socket error")
        
        proxy._handle_client(mock_socket, ("127.0.0.1", 12345))
        
        # Should not crash and should close socket
        mock_socket.close.assert_called_once()
    
    @patch('socket.socket')
    def test_start_stop_proxy(self, mock_socket_class):
        """Test starting and stopping proxy"""
        proxy = HTTPProxy("127.0.0.1", 8080)
        
        # Mock socket
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        mock_socket.accept.side_effect = KeyboardInterrupt()  # Simulate Ctrl+C
        
        # Test start
        with pytest.raises(KeyboardInterrupt):
            proxy.start()
        
        assert proxy.running is False
        mock_socket.bind.assert_called_once_with(("127.0.0.1", 8080))
        mock_socket.listen.assert_called_once_with(5)
    
    def test_stop_proxy(self):
        """Test stopping proxy"""
        proxy = HTTPProxy()
        proxy.running = True
        proxy.server_socket = Mock()
        
        proxy.stop()
        
        assert proxy.running is False
        proxy.server_socket.close.assert_called_once()
    
    def test_stop_proxy_no_socket(self):
        """Test stopping proxy when no socket exists"""
        proxy = HTTPProxy()
        proxy.running = True
        proxy.server_socket = None
        
        # Should not crash
        proxy.stop()
        assert proxy.running is False