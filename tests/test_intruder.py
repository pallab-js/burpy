"""
Tests for intruder functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor
from burpy.tools.intruder import Intruder


class TestIntruder:
    """Test cases for Intruder class"""
    
    def test_intruder_initialization(self):
        """Test intruder initialization"""
        intruder = Intruder(max_threads=5)
        assert intruder.max_threads == 5
        assert intruder.session is not None
        assert intruder.session.verify is False
    
    def test_intruder_default_initialization(self):
        """Test intruder initialization with default values"""
        intruder = Intruder()
        assert intruder.max_threads == 10
        assert intruder.session is not None
    
    @patch('requests.Session.request')
    def test_fuzz_parameter_success(self, mock_request):
        """Test successful parameter fuzzing"""
        intruder = Intruder(max_threads=2)
        
        # Mock responses for different payloads
        responses = [
            Mock(status_code=200, text="Normal response", url="https://example.com?test=admin"),
            Mock(status_code=404, text="Not found", url="https://example.com?test=test"),
            Mock(status_code=500, text="Server error", url="https://example.com?test=user")
        ]
        mock_request.side_effect = responses
        
        wordlist = ["admin", "test", "user"]
        results = intruder.fuzz_parameter("https://example.com", "test", wordlist)
        
        assert len(results) == 3
        assert all(r['success'] for r in results)
        assert results[0]['payload'] == "admin"
        assert results[0]['status_code'] == 200
        assert results[1]['payload'] == "test"
        assert results[1]['status_code'] == 404
        assert results[2]['payload'] == "user"
        assert results[2]['status_code'] == 500
    
    @patch('requests.Session.request')
    def test_fuzz_parameter_with_headers(self, mock_request):
        """Test parameter fuzzing with custom headers"""
        intruder = Intruder(max_threads=2)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_response.url = "https://example.com?test=admin"
        mock_request.return_value = mock_response
        
        headers = {"Authorization": "Bearer token123"}
        wordlist = ["admin"]
        results = intruder.fuzz_parameter("https://example.com", "test", wordlist, headers=headers)
        
        assert len(results) == 1
        assert results[0]['success'] is True
        mock_request.assert_called_with(
            method="GET",
            url="https://example.com",
            params={"test": "admin"},
            headers=headers,
            timeout=10
        )
    
    @patch('requests.Session.request')
    def test_fuzz_parameter_error(self, mock_request):
        """Test parameter fuzzing with errors"""
        intruder = Intruder(max_threads=2)
        mock_request.side_effect = Exception("Connection error")
        
        wordlist = ["admin", "test"]
        results = intruder.fuzz_parameter("https://example.com", "test", wordlist)
        
        assert len(results) == 2
        assert all(not r['success'] for r in results)
        assert all("Connection error" in r['error'] for r in results)
    
    @patch('requests.Session.request')
    def test_brute_force_auth_success(self, mock_request):
        """Test successful authentication brute force"""
        intruder = Intruder(max_threads=2)
        
        # Mock responses - one successful login
        responses = [
            Mock(status_code=401, text="Unauthorized", url="https://example.com/login"),
            Mock(status_code=200, text="Welcome admin", url="https://example.com/login"),
            Mock(status_code=401, text="Unauthorized", url="https://example.com/login"),
            Mock(status_code=401, text="Unauthorized", url="https://example.com/login")
        ]
        mock_request.side_effect = responses
        
        usernames = ["admin", "user"]
        passwords = ["password", "123456"]
        results = intruder.brute_force_auth(
            "https://example.com/login", "username", "password", usernames, passwords
        )
        
        assert len(results) == 4  # 2 usernames * 2 passwords
        success_results = [r for r in results if r['success'] and r['status_code'] == 200]
        assert len(success_results) == 1
        assert success_results[0]['username'] == "admin"
        assert success_results[0]['password'] == "password"
    
    @patch('requests.Session.request')
    def test_brute_force_auth_with_headers(self, mock_request):
        """Test authentication brute force with custom headers"""
        intruder = Intruder(max_threads=2)
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.url = "https://example.com/login"
        mock_request.return_value = mock_response
        
        headers = {"Content-Type": "application/json"}
        usernames = ["admin"]
        passwords = ["password"]
        results = intruder.brute_force_auth(
            "https://example.com/login", "username", "password", usernames, passwords, headers=headers
        )
        
        assert len(results) == 1
        mock_request.assert_called_with(
            method="POST",
            url="https://example.com/login",
            data={"username": "admin", "password": "password"},
            headers=headers,
            timeout=10
        )
    
    @patch('requests.Session.request')
    def test_brute_force_auth_error(self, mock_request):
        """Test authentication brute force with errors"""
        intruder = Intruder(max_threads=2)
        mock_request.side_effect = Exception("Network error")
        
        usernames = ["admin"]
        passwords = ["password"]
        results = intruder.brute_force_auth(
            "https://example.com/login", "username", "password", usernames, passwords
        )
        
        assert len(results) == 1
        assert not results[0]['success']
        assert "Network error" in results[0]['error']
    
    @patch('requests.Session.get')
    def test_directory_brute_force_success(self, mock_get):
        """Test successful directory brute force"""
        intruder = Intruder(max_threads=2)
        
        # Mock responses for different paths
        responses = [
            Mock(status_code=404, text="Not found", url="https://example.com/admin"),
            Mock(status_code=200, text="Admin panel", url="https://example.com/login"),
            Mock(status_code=403, text="Forbidden", url="https://example.com/private")
        ]
        mock_get.side_effect = responses
        
        wordlist = ["admin", "login", "private"]
        results = intruder.directory_brute_force("https://example.com", wordlist)
        
        assert len(results) == 3
        assert all(r['success'] for r in results)
        assert results[0]['path'] == "admin"
        assert results[0]['status_code'] == 404
        assert results[1]['path'] == "login"
        assert results[1]['status_code'] == 200
        assert results[2]['path'] == "private"
        assert results[2]['status_code'] == 403
    
    @patch('requests.Session.get')
    def test_directory_brute_force_error(self, mock_get):
        """Test directory brute force with errors"""
        intruder = Intruder(max_threads=2)
        mock_get.side_effect = Exception("Connection failed")
        
        wordlist = ["admin", "test"]
        results = intruder.directory_brute_force("https://example.com", wordlist)
        
        assert len(results) == 2
        assert all(not r['success'] for r in results)
        assert all("Connection failed" in r['error'] for r in results)
    
    @patch('requests.Session.get')
    def test_sql_injection_test_default_payloads(self, mock_get):
        """Test SQL injection testing with default payloads"""
        intruder = Intruder(max_threads=2)
        
        # Mock responses - one with SQL error
        responses = [
            Mock(status_code=200, text="Normal response", url="https://example.com?test=admin"),
            Mock(status_code=200, text="Error: SQL syntax error", url="https://example.com?test=' OR '1'='1"),
            Mock(status_code=200, text="Normal response", url="https://example.com?test=test"),
            Mock(status_code=200, text="Normal response", url="https://example.com?test=user")
        ]
        mock_get.side_effect = responses
        
        results = intruder.sql_injection_test("https://example.com", "test")
        
        assert len(results) > 0
        sql_error_results = [r for r in results if r['has_sql_error']]
        assert len(sql_error_results) > 0
        assert any("' OR '1'='1" in r['payload'] for r in sql_error_results)
    
    @patch('requests.Session.get')
    def test_sql_injection_test_custom_payloads(self, mock_get):
        """Test SQL injection testing with custom payloads"""
        intruder = Intruder(max_threads=2)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Normal response"
        mock_response.url = "https://example.com?test=custom"
        mock_get.return_value = mock_response
        
        custom_payloads = ["custom1", "custom2"]
        results = intruder.sql_injection_test("https://example.com", "test", custom_payloads)
        
        assert len(results) == 2
        assert all(r['success'] for r in results)
        assert all(r['payload'] in custom_payloads for r in results)
    
    @patch('requests.Session.get')
    def test_sql_injection_test_error_indicators(self, mock_get):
        """Test SQL injection testing with various error indicators"""
        intruder = Intruder(max_threads=2)
        
        # Mock responses with different SQL error indicators
        responses = [
            Mock(status_code=200, text="MySQL error occurred", url="https://example.com?test=1"),
            Mock(status_code=200, text="PostgreSQL syntax error", url="https://example.com?test=2"),
            Mock(status_code=200, text="Oracle database error", url="https://example.com?test=3"),
            Mock(status_code=200, text="SQLite query failed", url="https://example.com?test=4"),
            Mock(status_code=200, text="Normal response", url="https://example.com?test=5")
        ]
        mock_get.side_effect = responses
        
        results = intruder.sql_injection_test("https://example.com", "test")
        
        assert len(results) > 0
        sql_error_results = [r for r in results if r['has_sql_error']]
        assert len(sql_error_results) >= 4  # At least 4 should have SQL errors
    
    @patch('requests.Session.get')
    def test_sql_injection_test_error(self, mock_get):
        """Test SQL injection testing with errors"""
        intruder = Intruder(max_threads=2)
        mock_get.side_effect = Exception("Connection error")
        
        results = intruder.sql_injection_test("https://example.com", "test")
        
        assert len(results) > 0
        assert all(not r['success'] for r in results)
        assert all("Connection error" in r['error'] for r in results)
    
    def test_thread_pool_execution(self):
        """Test that thread pool execution works correctly"""
        intruder = Intruder(max_threads=3)
        
        # Test that the intruder can handle concurrent execution
        # This is more of an integration test
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Success"
            mock_response.url = "https://example.com"
            mock_request.return_value = mock_response
            
            wordlist = ["test1", "test2", "test3"]
            results = intruder.fuzz_parameter("https://example.com", "test", wordlist)
            
            assert len(results) == 3
            assert all(r['success'] for r in results)
    
    def test_max_threads_limitation(self):
        """Test that max_threads parameter is respected"""
        intruder = Intruder(max_threads=1)
        
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Success"
            mock_response.url = "https://example.com"
            mock_request.return_value = mock_response
            
            # Use a large wordlist to test thread limiting
            wordlist = ["test"] * 10
            results = intruder.fuzz_parameter("https://example.com", "test", wordlist)
            
            assert len(results) == 10
            assert all(r['success'] for r in results)
    
    def test_empty_wordlist(self):
        """Test handling of empty wordlist"""
        intruder = Intruder(max_threads=2)
        
        results = intruder.fuzz_parameter("https://example.com", "test", [])
        assert len(results) == 0
    
    def test_empty_usernames_passwords(self):
        """Test handling of empty usernames/passwords lists"""
        intruder = Intruder(max_threads=2)
        
        results = intruder.brute_force_auth(
            "https://example.com/login", "username", "password", [], []
        )
        assert len(results) == 0