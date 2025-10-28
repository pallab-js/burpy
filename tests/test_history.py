"""
Tests for history logger functionality
"""

import pytest
import json
import os
import tempfile
from unittest.mock import patch, mock_open
from burpy.history.logger import HistoryLogger


class TestHistoryLogger:
    """Test cases for HistoryLogger class"""
    
    def test_logger_initialization(self):
        """Test logger initialization"""
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            logger = HistoryLogger(temp_file)
            assert logger.log_file == temp_file
            assert logger.history == []
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_logger_initialization_with_existing_file(self):
        """Test logger initialization with existing history file"""
        test_data = [
            {
                'id': 1,
                'timestamp': '2024-01-01T00:00:00',
                'request': {'method': 'GET', 'url': 'https://example.com'},
                'response': {'status_code': 200}
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            logger = HistoryLogger(temp_file)
            assert len(logger.history) == 1
            assert logger.history[0]['id'] == 1
        finally:
            os.unlink(temp_file)
    
    def test_log_request_without_response(self, isolated_history_logger):
        """Test logging request without response"""
        logger = isolated_history_logger
        
        request = {
            'method': 'GET',
            'url': 'https://example.com/test',
            'headers': {'User-Agent': 'Burpy-Test'},
            'body': 'test data'
        }
        
        logger.log_request(request)
        
        assert len(logger.history) == 1
        assert logger.history[0]['request'] == request
        assert logger.history[0]['response'] is None
        assert logger.history[0]['id'] == 1
        assert 'timestamp' in logger.history[0]
    
    def test_log_request_with_response(self):
        """Test logging request with response"""
        logger = HistoryLogger("test_history.json")
        
        request = {
            'method': 'POST',
            'url': 'https://example.com/api',
            'headers': {'Content-Type': 'application/json'},
            'body': '{"key": "value"}'
        }
        
        response = {
            'status_code': 201,
            'headers': {'Location': 'https://example.com/api/123'},
            'content': '{"id": 123}'
        }
        
        logger.log_request(request, response)
        
        assert len(logger.history) == 1
        assert logger.history[0]['request'] == request
        assert logger.history[0]['response'] == response
        assert logger.history[0]['id'] == 1
    
    def test_log_multiple_requests(self):
        """Test logging multiple requests"""
        logger = HistoryLogger("test_history.json")
        
        requests = [
            {'method': 'GET', 'url': 'https://example.com/1'},
            {'method': 'POST', 'url': 'https://example.com/2'},
            {'method': 'PUT', 'url': 'https://example.com/3'}
        ]
        
        for req in requests:
            logger.log_request(req)
        
        assert len(logger.history) == 3
        assert logger.history[0]['id'] == 1
        assert logger.history[1]['id'] == 2
        assert logger.history[2]['id'] == 3
    
    def test_get_history_without_limit(self):
        """Test getting all history without limit"""
        logger = HistoryLogger("test_history.json")
        
        # Add some test data
        for i in range(5):
            logger.log_request({'method': 'GET', 'url': f'https://example.com/{i}'})
        
        history = logger.get_history()
        assert len(history) == 5
    
    def test_get_history_with_limit(self):
        """Test getting history with limit"""
        logger = HistoryLogger("test_history.json")
        
        # Add some test data
        for i in range(10):
            logger.log_request({'method': 'GET', 'url': f'https://example.com/{i}'})
        
        history = logger.get_history(limit=3)
        assert len(history) == 3
        # Should return the last 3 entries
        assert history[0]['url'] == 'https://example.com/7'
        assert history[1]['url'] == 'https://example.com/8'
        assert history[2]['url'] == 'https://example.com/9'
    
    def test_get_request_by_id(self):
        """Test getting specific request by ID"""
        logger = HistoryLogger("test_history.json")
        
        # Add some test data
        for i in range(3):
            logger.log_request({'method': 'GET', 'url': f'https://example.com/{i}'})
        
        # Test getting existing request
        request = logger.get_request(2)
        assert request is not None
        assert request['id'] == 2
        assert request['url'] == 'https://example.com/1'
        
        # Test getting non-existent request
        request = logger.get_request(999)
        assert request is None
    
    def test_search_history_by_url(self):
        """Test searching history by URL"""
        logger = HistoryLogger("test_history.json")
        
        # Add test data
        logger.log_request({'method': 'GET', 'url': 'https://example.com/login'})
        logger.log_request({'method': 'POST', 'url': 'https://api.example.com/users'})
        logger.log_request({'method': 'GET', 'url': 'https://example.com/dashboard'})
        
        # Search by URL
        results = logger.search_history("login")
        assert len(results) == 1
        assert results[0]['url'] == 'https://example.com/login'
        
        results = logger.search_history("example.com")
        assert len(results) == 2  # login and dashboard
    
    def test_search_history_by_method(self):
        """Test searching history by HTTP method"""
        logger = HistoryLogger("test_history.json")
        
        # Add test data
        logger.log_request({'method': 'GET', 'url': 'https://example.com/1'})
        logger.log_request({'method': 'POST', 'url': 'https://example.com/2'})
        logger.log_request({'method': 'PUT', 'url': 'https://example.com/3'})
        
        # Search by method
        results = logger.search_history("POST")
        assert len(results) == 1
        assert results[0]['method'] == 'POST'
    
    def test_search_history_by_body(self):
        """Test searching history by request body"""
        logger = HistoryLogger("test_history.json")
        
        # Add test data
        logger.log_request({'method': 'POST', 'url': 'https://example.com/api', 'body': '{"user": "admin"}'})
        logger.log_request({'method': 'POST', 'url': 'https://example.com/login', 'body': '{"user": "guest"}'})
        logger.log_request({'method': 'GET', 'url': 'https://example.com/dashboard', 'body': ''})
        
        # Search by body content
        results = logger.search_history("admin")
        assert len(results) == 1
        assert "admin" in results[0]['body']
    
    def test_search_history_case_insensitive(self):
        """Test case-insensitive search"""
        logger = HistoryLogger("test_history.json")
        
        logger.log_request({'method': 'GET', 'url': 'https://EXAMPLE.COM/Test'})
        
        results = logger.search_history("example")
        assert len(results) == 1
        
        results = logger.search_history("TEST")
        assert len(results) == 1
    
    def test_search_history_no_results(self):
        """Test search with no results"""
        logger = HistoryLogger("test_history.json")
        
        logger.log_request({'method': 'GET', 'url': 'https://example.com/test'})
        
        results = logger.search_history("nonexistent")
        assert len(results) == 0
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_history(self, mock_json_dump, mock_file):
        """Test saving history to file"""
        logger = HistoryLogger("test_history.json")
        
        # Add some test data
        logger.log_request({'method': 'GET', 'url': 'https://example.com/test'})
        
        logger.save_history()
        
        # Check that the file was opened for writing
        write_calls = [call for call in mock_file.call_args_list if call[0][1] == 'w']
        assert len(write_calls) >= 1
        mock_json_dump.assert_called()
    
    @patch('builtins.open', new_callable=mock_open, read_data='[{"id": 1, "test": "data"}]')
    @patch('json.load')
    def test_load_history_success(self, mock_json_load, mock_file):
        """Test successful loading of history from file"""
        mock_json_load.return_value = [{"id": 1, "test": "data"}]
        
        logger = HistoryLogger("test_history.json")
        
        mock_file.assert_called_once_with("test_history.json", 'r')
        mock_json_load.assert_called_once()
        assert logger.history == [{"id": 1, "test": "data"}]
    
    @patch('os.path.exists')
    @patch('builtins.open', side_effect=IOError("File not found"))
    def test_load_history_file_not_exists(self, mock_file, mock_exists):
        """Test loading history when file doesn't exist"""
        mock_exists.return_value = False
        
        logger = HistoryLogger("test_history.json")
        
        assert logger.history == []
        mock_file.assert_not_called()
    
    @patch('os.path.exists')
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_load_history_error(self, mock_file, mock_exists):
        """Test loading history with error"""
        mock_exists.return_value = True
        
        logger = HistoryLogger("test_history.json")
        
        assert logger.history == []
    
    def test_clear_history(self):
        """Test clearing history"""
        logger = HistoryLogger("test_history.json")
        
        # Add some test data
        for i in range(3):
            logger.log_request({'method': 'GET', 'url': f'https://example.com/{i}'})
        
        assert len(logger.history) == 3
        
        logger.clear_history()
        
        assert len(logger.history) == 0
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_export_history(self, mock_json_dump, mock_file):
        """Test exporting history to file"""
        logger = HistoryLogger("test_history.json")
        
        # Add some test data
        logger.log_request({'method': 'GET', 'url': 'https://example.com/test'})
        
        logger.export_history("exported_history.json")
        
        # Check that the file was opened for writing
        write_calls = [call for call in mock_file.call_args_list if call[0][1] == 'w']
        assert len(write_calls) >= 1
        mock_json_dump.assert_called()
    
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_export_history_error(self, mock_file):
        """Test exporting history with error"""
        logger = HistoryLogger("test_history.json")
        
        # Should not raise exception
        logger.export_history("exported_history.json")
    
    def test_history_entry_structure(self):
        """Test that history entries have correct structure"""
        logger = HistoryLogger("test_history.json")
        
        request = {
            'method': 'POST',
            'url': 'https://example.com/api',
            'headers': {'Content-Type': 'application/json'},
            'body': '{"data": "test"}'
        }
        
        response = {
            'status_code': 201,
            'headers': {'Location': '/api/123'},
            'content': '{"id": 123}'
        }
        
        logger.log_request(request, response)
        
        entry = logger.history[0]
        
        # Check required fields
        assert 'id' in entry
        assert 'timestamp' in entry
        assert 'request' in entry
        assert 'response' in entry
        
        # Check data integrity
        assert entry['request'] == request
        assert entry['response'] == response
        assert entry['id'] == 1
        assert isinstance(entry['timestamp'], str)
    
    def test_auto_increment_id(self):
        """Test that IDs are auto-incremented correctly"""
        logger = HistoryLogger("test_history.json")
        
        # Add multiple requests
        for i in range(5):
            logger.log_request({'method': 'GET', 'url': f'https://example.com/{i}'})
        
        # Check IDs are sequential
        for i, entry in enumerate(logger.history):
            assert entry['id'] == i + 1