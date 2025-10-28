"""
Integration tests for Burpy components
"""

import pytest
import tempfile
import os
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from burpy.core.proxy import HTTPProxy
from burpy.scanner.vulnerability_scanner import VulnerabilityScanner
from burpy.tools.repeater import RequestRepeater
from burpy.tools.intruder import Intruder
from burpy.history.logger import HistoryLogger
from burpy.config.settings import Config


class TestIntegration:
    """Integration tests for Burpy components"""
    
    def test_proxy_with_history_logging(self):
        """Test proxy integration with history logging"""
        proxy = HTTPProxy("127.0.0.1", 8081)
        logger = HistoryLogger("test_integration_history.json")
        
        # Add request handler for logging
        def log_request(request):
            logger.log_request(request)
            return request
        
        proxy.add_request_handler(log_request)
        
        # Test request parsing and logging
        test_request = {
            'method': 'GET',
            'url': 'https://example.com/test',
            'version': 'HTTP/1.1',
            'headers': {'Host': 'example.com'},
            'body': ''
        }
        
        # Simulate request handling
        log_request(test_request)
        
        # Check that request was logged
        history = logger.get_history()
        assert len(history) == 1
        assert history[0]['request']['method'] == 'GET'
        assert history[0]['request']['url'] == 'https://example.com/test'
        
        # Clean up
        if os.path.exists("test_integration_history.json"):
            os.remove("test_integration_history.json")
    
    def test_scanner_with_config(self):
        """Test scanner integration with configuration"""
        config = Config("test_integration_config.json")
        config.set('scanner.timeout', 5)
        config.set('scanner.max_threads', 2)
        
        scanner = VulnerabilityScanner()
        scanner.session.timeout = config.get('scanner.timeout')
        
        assert scanner.session.timeout == 5
        
        # Clean up
        if os.path.exists("test_integration_config.json"):
            os.remove("test_integration_config.json")
    
    @patch('requests.Session.get')
    def test_repeater_with_scanner_integration(self, mock_get):
        """Test repeater integration with scanner"""
        repeater = RequestRepeater()
        scanner = VulnerabilityScanner()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Test response"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.url = "https://example.com/test"
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_get.return_value = mock_response
        
        # Use repeater to send request
        response = repeater.send_request("GET", "https://example.com/test")
        
        # Use scanner to analyze the same URL
        scan_results = scanner.scan_url("https://example.com/test")
        
        assert response['success'] is True
        assert len(scan_results) > 0
    
    def test_intruder_with_history_integration(self):
        """Test intruder integration with history logging"""
        intruder = Intruder(max_threads=2)
        logger = HistoryLogger("test_intruder_history.json")
        
        # Mock requests for intruder
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Success"
            mock_response.url = "https://example.com?test=admin"
            mock_request.return_value = mock_response
            
            # Run fuzzing
            results = intruder.fuzz_parameter("https://example.com", "test", ["admin", "test"])
            
            # Log results
            for result in results:
                if result['success']:
                    request = {
                        'method': 'GET',
                        'url': result['url'],
                        'headers': {},
                        'body': ''
                    }
                    logger.log_request(request)
        
        # Check that requests were logged
        history = logger.get_history()
        assert len(history) == 2  # Two successful requests
        
        # Clean up
        if os.path.exists("test_intruder_history.json"):
            os.remove("test_intruder_history.json")
    
    def test_config_persistence_across_modules(self):
        """Test that configuration persists across different modules"""
        config_file = "test_persistence_config.json"
        config = Config(config_file)
        
        # Set some configuration values
        config.set('proxy.host', '192.168.1.1')
        config.set('scanner.timeout', 15)
        config.set('intruder.max_threads', 5)
        
        # Create new config instance (simulates module restart)
        config2 = Config(config_file)
        
        # Check that values persisted
        assert config2.get('proxy.host') == '192.168.1.1'
        assert config2.get('scanner.timeout') == 15
        assert config2.get('intruder.max_threads') == 5
        
        # Clean up
        if os.path.exists(config_file):
            os.remove(config_file)
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        # Initialize all components
        config = Config("test_e2e_config.json")
        logger = HistoryLogger("test_e2e_history.json")
        repeater = RequestRepeater()
        scanner = VulnerabilityScanner()
        intruder = Intruder(max_threads=2)
        
        # Configure components
        config.set('scanner.timeout', 5)
        scanner.session.timeout = config.get('scanner.timeout')
        
        with patch('requests.Session.request') as mock_request:
            # Mock responses for different operations
            responses = [
                # Repeater response
                Mock(status_code=200, text="API Response", headers={}, url="https://api.example.com/users", elapsed=Mock(total_seconds=Mock(return_value=0.1))),
                # Scanner responses
                Mock(status_code=200, text="Page content", headers={}, url="https://example.com"),
                Mock(status_code=200, text="Normal response", headers={}, url="https://example.com?test=admin"),
                Mock(status_code=200, text="Normal response", headers={}, url="https://example.com?test=test"),
            ]
            mock_request.side_effect = responses
            
            # 1. Use repeater to test API endpoint
            api_response = repeater.send_request("GET", "https://api.example.com/users")
            assert api_response['success'] is True
            
            # Log the request
            logger.log_request({
                'method': 'GET',
                'url': 'https://api.example.com/users',
                'headers': {},
                'body': ''
            })
            
            # 2. Scan the main site for vulnerabilities
            scan_results = scanner.scan_url("https://example.com")
            assert len(scan_results) > 0
            
            # 3. Use intruder to fuzz parameters
            fuzz_results = intruder.fuzz_parameter("https://example.com", "test", ["admin", "test"])
            assert len(fuzz_results) == 2
            
            # 4. Check history
            history = logger.get_history()
            assert len(history) == 1
            
            # 5. Search history
            search_results = logger.search_history("api")
            assert len(search_results) == 1
        
        # Clean up
        for file in ["test_e2e_config.json", "test_e2e_history.json"]:
            if os.path.exists(file):
                os.remove(file)
    
    def test_error_handling_integration(self):
        """Test error handling across integrated components"""
        logger = HistoryLogger("test_error_history.json")
        repeater = RequestRepeater()
        
        with patch('requests.Session.request', side_effect=Exception("Network error")):
            # Test that errors are handled gracefully
            response = repeater.send_request("GET", "https://example.com")
            assert response['success'] is False
            assert "Network error" in response['error']
            
            # Log the failed request
            logger.log_request({
                'method': 'GET',
                'url': 'https://example.com',
                'headers': {},
                'body': ''
            })
        
        # Check that failed request was still logged
        history = logger.get_history()
        assert len(history) == 1
        
        # Clean up
        if os.path.exists("test_error_history.json"):
            os.remove("test_error_history.json")
    
    def test_concurrent_operations(self):
        """Test concurrent operations across components"""
        logger = HistoryLogger("test_concurrent_history.json")
        intruder = Intruder(max_threads=3)
        
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Success"
            mock_response.url = "https://example.com"
            mock_request.return_value = mock_response
            
            # Run concurrent fuzzing operations
            results = intruder.fuzz_parameter("https://example.com", "test", ["admin", "test", "user"])
            
            # Log all results
            for result in results:
                if result['success']:
                    logger.log_request({
                        'method': 'GET',
                        'url': result['url'],
                        'headers': {},
                        'body': ''
                    })
        
        # Check that all requests were logged
        history = logger.get_history()
        assert len(history) == 3
        
        # Clean up
        if os.path.exists("test_concurrent_history.json"):
            os.remove("test_concurrent_history.json")
    
    def test_data_consistency_across_modules(self):
        """Test that data remains consistent across modules"""
        logger = HistoryLogger("test_consistency_history.json")
        
        # Add some test data
        test_requests = [
            {'method': 'GET', 'url': 'https://example.com/1', 'headers': {}, 'body': ''},
            {'method': 'POST', 'url': 'https://example.com/2', 'headers': {}, 'body': 'data'},
            {'method': 'PUT', 'url': 'https://example.com/3', 'headers': {}, 'body': 'update'}
        ]
        
        for req in test_requests:
            logger.log_request(req)
        
        # Test search functionality
        get_results = logger.search_history("GET")
        post_results = logger.search_history("POST")
        put_results = logger.search_history("PUT")
        
        assert len(get_results) == 1
        assert len(post_results) == 1
        assert len(put_results) == 1
        
        # Test that data is consistent
        assert get_results[0]['request']['method'] == 'GET'
        assert post_results[0]['request']['method'] == 'POST'
        assert put_results[0]['request']['method'] == 'PUT'
        
        # Clean up
        if os.path.exists("test_consistency_history.json"):
            os.remove("test_consistency_history.json")
    
    def test_memory_usage_with_large_datasets(self):
        """Test memory usage with large datasets"""
        logger = HistoryLogger("test_memory_history.json")
        
        # Add many requests to test memory usage
        for i in range(100):
            logger.log_request({
                'method': 'GET',
                'url': f'https://example.com/page{i}',
                'headers': {'User-Agent': f'Test-{i}'},
                'body': f'data-{i}'
            })
        
        # Test that all data is accessible
        history = logger.get_history()
        assert len(history) == 100
        
        # Test search performance
        search_results = logger.search_history("page50")
        assert len(search_results) == 1
        assert "page50" in search_results[0]['request']['url']
        
        # Clean up
        if os.path.exists("test_memory_history.json"):
            os.remove("test_memory_history.json")