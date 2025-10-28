"""
Pytest configuration and fixtures
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch
import threading
import time


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_requests():
    """Mock requests library"""
    with patch('requests.request') as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Test response"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_response.url = "https://example.com/test"
        mock_request.return_value = mock_response
        yield mock_request


@pytest.fixture
def sample_request():
    """Sample HTTP request for testing"""
    return {
        'method': 'GET',
        'url': 'https://example.com/test',
        'version': 'HTTP/1.1',
        'headers': {
            'Host': 'example.com',
            'User-Agent': 'Burpy-Test/1.0'
        },
        'body': 'test data',
        'raw': 'GET /test HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Burpy-Test/1.0\r\n\r\ntest data'
    }


@pytest.fixture
def sample_response():
    """Sample HTTP response for testing"""
    return {
        'success': True,
        'status_code': 200,
        'headers': {'Content-Type': 'text/html'},
        'content': 'Test response content',
        'url': 'https://example.com/test',
        'elapsed_time': 0.1
    }


@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        'proxy': {
            'host': '127.0.0.1',
            'port': 8080,
            'enabled': True
        },
        'scanner': {
            'timeout': 5,
            'max_threads': 2
        }
    }


@pytest.fixture
def isolated_history_logger():
    """Create an isolated history logger for testing"""
    import tempfile
    import os
    from burpy.history.logger import HistoryLogger
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_file = f.name
    
    logger = HistoryLogger(temp_file)
    
    yield logger
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def isolated_config():
    """Create an isolated config for testing"""
    import tempfile
    import os
    from burpy.config.settings import Config
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_file = f.name
    
    config = Config(temp_file)
    
    yield config
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)