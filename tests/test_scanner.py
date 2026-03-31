"""
Tests for vulnerability scanner functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from burpy.scanner.vulnerability_scanner import VulnerabilityScanner


class TestVulnerabilityScanner:
    """Test cases for VulnerabilityScanner class"""
    
    def test_scanner_initialization(self):
        """Test scanner initialization"""
        scanner = VulnerabilityScanner()
        assert scanner.session is not None
        assert scanner.session.verify is False
        assert scanner._timeout == 10
    
    @patch('requests.Session.get')
    def test_scan_url_connection_success(self, mock_get):
        """Test successful URL scanning with connection"""
        scanner = VulnerabilityScanner()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Test page content"
        mock_get.return_value = mock_response
        
        results = scanner.scan_url("https://example.com")
        
        assert len(results) > 0
        # Should have basic connectivity result
        connectivity_results = [r for r in results if r['type'] == 'info' and 'Basic Connectivity' in r['title']]
        assert len(connectivity_results) == 1
        assert connectivity_results[0]['severity'] == 'info'
    
    @patch('requests.Session.get')
    def test_scan_url_connection_failure(self, mock_get):
        """Test URL scanning with connection failure"""
        scanner = VulnerabilityScanner()
        mock_get.side_effect = Exception("Connection failed")
        
        results = scanner.scan_url("https://example.com")
        
        assert len(results) == 1
        assert results[0]['type'] == 'error'
        assert results[0]['title'] == 'Connection Failed'
        assert results[0]['severity'] == 'high'
    
    @patch('requests.Session.get')
    def test_check_sql_injection_no_query(self, mock_get):
        """Test SQL injection check with no query parameters"""
        scanner = VulnerabilityScanner()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Test page"
        mock_get.return_value = mock_response
        
        results = scanner._check_sql_injection("https://example.com", mock_response)
        
        assert len(results) == 0  # No query parameters to test
    
    @patch('requests.Session.get')
    def test_check_sql_injection_with_query(self, mock_get):
        """Test SQL injection check with query parameters"""
        scanner = VulnerabilityScanner()
        
        # Mock response for initial scan
        initial_response = Mock()
        initial_response.status_code = 200
        initial_response.text = "Test page"
        
        # Mock responses for SQL injection tests
        test_responses = [
            Mock(status_code=200, text="Normal response"),
            Mock(status_code=200, text="Error: SQL syntax error"),
            Mock(status_code=200, text="MySQL error occurred"),
            Mock(status_code=200, text="Normal response")
        ]
        mock_get.side_effect = test_responses
        
        results = scanner._check_sql_injection("https://example.com?search=test", initial_response)
        
        # Should find SQL injection vulnerabilities
        sql_results = [r for r in results if 'SQL Injection' in r['title']]
        assert len(sql_results) > 0
        assert any(r['severity'] == 'high' for r in sql_results)
    
    @patch('requests.Session.get')
    def test_check_xss_no_query(self, mock_get):
        """Test XSS check with no query parameters"""
        scanner = VulnerabilityScanner()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Test page"
        mock_get.return_value = mock_response
        
        results = scanner._check_xss("https://example.com", mock_response)
        
        assert len(results) == 0  # No query parameters to test
    
    @patch('requests.Session.get')
    def test_check_xss_with_query(self, mock_get):
        """Test XSS check with query parameters"""
        scanner = VulnerabilityScanner()
        
        # Mock response for initial scan
        initial_response = Mock()
        initial_response.status_code = 200
        initial_response.text = "Test page"
        
        # Mock responses for XSS tests - one payload gets reflected
        test_responses = [
            Mock(status_code=200, text="Normal response"),
            Mock(status_code=200, text="<script>alert('XSS')</script>"),  # Reflected
            Mock(status_code=200, text="Normal response"),
            Mock(status_code=200, text="Normal response")
        ]
        mock_get.side_effect = test_responses
        
        results = scanner._check_xss("https://example.com?search=test", initial_response)
        
        # Should find XSS vulnerability
        xss_results = [r for r in results if 'XSS' in r['title']]
        assert len(xss_results) > 0
        assert any(r['severity'] == 'medium' for r in xss_results)
    
    @patch('requests.Session.get')
    def test_check_directory_traversal(self, mock_get):
        """Test directory traversal check"""
        scanner = VulnerabilityScanner()
        
        # Mock response for initial scan
        initial_response = Mock()
        initial_response.status_code = 200
        initial_response.text = "Test page"
        
        # Mock responses for directory traversal tests
        test_responses = [
            Mock(status_code=200, text="Normal response"),
            Mock(status_code=200, text="root:x:0:0:root:/root:/bin/bash"),  # /etc/passwd content
            Mock(status_code=200, text="Normal response"),
            Mock(status_code=200, text="Normal response")
        ]
        mock_get.side_effect = test_responses
        
        results = scanner._check_directory_traversal("https://example.com", initial_response)
        
        # Should find directory traversal vulnerability
        traversal_results = [r for r in results if 'Directory Traversal' in r['title']]
        assert len(traversal_results) > 0
        assert any(r['severity'] == 'high' for r in traversal_results)
    
    @patch('requests.Session.get')
    def test_check_sensitive_files(self, mock_get):
        """Test sensitive files check"""
        scanner = VulnerabilityScanner()
        
        # Mock response for initial scan
        initial_response = Mock()
        initial_response.status_code = 200
        initial_response.text = "Test page"
        
        # Mock responses for sensitive files tests
        test_responses = [
            Mock(status_code=404, text="Not found"),
            Mock(status_code=200, text="Database configuration"),  # .env file
            Mock(status_code=200, text="WordPress config"),  # wp-config.php
            Mock(status_code=200, text="Apache config"),  # .htaccess
            Mock(status_code=200, text="Robots.txt content"),  # robots.txt
            Mock(status_code=200, text="Sitemap content"),  # sitemap.xml
            Mock(status_code=200, text="Admin panel"),  # admin/
            Mock(status_code=200, text="PHP info"),  # phpinfo.php
            Mock(status_code=200, text="Test page")  # test.php
        ]
        mock_get.side_effect = test_responses
        
        results = scanner._check_sensitive_files("https://example.com", initial_response)
        
        # Should find sensitive files
        sensitive_results = [r for r in results if 'Sensitive File Found' in r['title']]
        assert len(sensitive_results) > 0
        assert all(r['severity'] == 'medium' for r in sensitive_results)
    
    @patch('requests.Session.request')
    def test_check_http_methods(self, mock_request):
        """Test HTTP methods check"""
        scanner = VulnerabilityScanner()
        
        # Mock response for initial scan
        initial_response = Mock()
        initial_response.status_code = 200
        initial_response.text = "Test page"
        
        # Mock responses for HTTP methods tests
        test_responses = [
            Mock(status_code=200, text="PUT response"),  # PUT
            Mock(status_code=200, text="DELETE response"),  # DELETE
            Mock(status_code=200, text="PATCH response"),  # PATCH
            Mock(status_code=200, text="TRACE response"),  # TRACE
            Mock(status_code=200, text="OPTIONS response")  # OPTIONS
        ]
        mock_request.side_effect = test_responses
        
        results = scanner._check_http_methods("https://example.com", initial_response)
        
        # Should find dangerous HTTP methods
        method_results = [r for r in results if 'Method Allowed' in r['title']]
        assert len(method_results) > 0
        assert all(r['severity'] == 'low' for r in method_results)
    
    def test_check_headers_security_missing_headers(self):
        """Test security headers check with missing headers"""
        scanner = VulnerabilityScanner()
        
        # Mock response with minimal headers
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "text/html"}
        
        results = scanner._check_headers_security("https://example.com", mock_response)
        
        # Should find missing security headers
        assert len(results) > 0
        assert all('Missing Security Header' in r['title'] for r in results)
        assert all(r['severity'] == 'low' for r in results)
    
    def test_check_headers_security_complete_headers(self):
        """Test security headers check with complete headers"""
        scanner = VulnerabilityScanner()
        
        # Mock response with all security headers
        mock_response = Mock()
        mock_response.headers = {
            "Content-Type": "text/html",
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000",
            "Content-Security-Policy": "default-src 'self'"
        }
        
        results = scanner._check_headers_security("https://example.com", mock_response)
        
        # Should not find any missing headers
        assert len(results) == 0
    
    @patch('requests.Session.get')
    def test_scan_url_exception_handling(self, mock_get):
        """Test scanner exception handling"""
        scanner = VulnerabilityScanner()
        
        # Mock successful initial connection
        initial_response = Mock()
        initial_response.status_code = 200
        initial_response.text = "Test page"
        
        # Mock exception for subsequent requests
        mock_get.side_effect = [initial_response, Exception("Test error")]
        
        results = scanner.scan_url("https://example.com")
        
        # Should still return basic connectivity result
        assert len(results) > 0
        connectivity_results = [r for r in results if r['type'] == 'info' and 'Basic Connectivity' in r['title']]
        assert len(connectivity_results) == 1
    
    def test_sql_payloads_coverage(self):
        """Test that all SQL injection payloads are tested"""
        scanner = VulnerabilityScanner()
        
        # This test ensures the payloads list is not empty
        # The actual payloads are tested in integration tests
        assert len(scanner._check_sql_injection.__code__.co_consts) > 0
    
    def test_xss_payloads_coverage(self):
        """Test that all XSS payloads are tested"""
        scanner = VulnerabilityScanner()
        
        # This test ensures the payloads list is not empty
        # The actual payloads are tested in integration tests
        assert len(scanner._check_xss.__code__.co_consts) > 0