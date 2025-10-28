"""
Tests for configuration functionality
"""

import pytest
import json
import os
import tempfile
from unittest.mock import patch, mock_open
from burpy.config.settings import Config


class TestConfig:
    """Test cases for Config class"""
    
    def test_config_initialization(self):
        """Test config initialization with default settings"""
        config = Config("test_config.json")
        assert config.config_file == "test_config.json"
        assert 'proxy' in config.settings
        assert 'scanner' in config.settings
        assert 'intruder' in config.settings
        assert 'history' in config.settings
        assert 'output' in config.settings
    
    def test_default_settings_structure(self):
        """Test that default settings have correct structure"""
        config = Config("test_config.json")
        settings = config.settings
        
        # Test proxy settings
        assert settings['proxy']['host'] == '127.0.0.1'
        assert settings['proxy']['port'] == 8080
        assert settings['proxy']['enabled'] is True
        
        # Test scanner settings
        assert settings['scanner']['timeout'] == 10
        assert settings['scanner']['max_threads'] == 5
        assert settings['scanner']['follow_redirects'] is True
        
        # Test intruder settings
        assert settings['intruder']['max_threads'] == 10
        assert settings['intruder']['delay'] == 0.1
        
        # Test history settings
        assert settings['history']['max_entries'] == 1000
        assert settings['history']['auto_save'] is True
        
        # Test output settings
        assert settings['output']['verbose'] is True
        assert settings['output']['color'] is True
        assert settings['output']['save_reports'] is True
    
    def test_get_simple_key(self):
        """Test getting simple configuration key"""
        config = Config("test_config.json")
        
        value = config.get('proxy.host')
        assert value == '127.0.0.1'
        
        value = config.get('scanner.timeout')
        assert value == 10
    
    def test_get_nested_key(self):
        """Test getting nested configuration key"""
        config = Config("test_config.json")
        
        value = config.get('proxy.host')
        assert value == '127.0.0.1'
        
        value = config.get('scanner.max_threads')
        assert value == 5
    
    def test_get_nonexistent_key(self):
        """Test getting non-existent configuration key"""
        config = Config("test_config.json")
        
        value = config.get('nonexistent.key')
        assert value is None
        
        value = config.get('nonexistent.key', 'default')
        assert value == 'default'
    
    def test_get_with_default_value(self):
        """Test getting key with default value"""
        config = Config("test_config.json")
        
        value = config.get('nonexistent.key', 'default_value')
        assert value == 'default_value'
    
    def test_set_simple_key(self):
        """Test setting simple configuration key"""
        config = Config("test_config.json")
        
        config.set('proxy.host', '0.0.0.0')
        assert config.get('proxy.host') == '0.0.0.0'
    
    def test_set_nested_key(self):
        """Test setting nested configuration key"""
        config = Config("test_config.json")
        
        config.set('scanner.timeout', 30)
        assert config.get('scanner.timeout') == 30
    
    def test_set_new_nested_key(self):
        """Test setting new nested configuration key"""
        config = Config("test_config.json")
        
        config.set('new.section.key', 'new_value')
        assert config.get('new.section.key') == 'new_value'
        assert config.settings['new']['section']['key'] == 'new_value'
    
    def test_set_multiple_keys(self):
        """Test setting multiple configuration keys"""
        config = Config("test_config.json")
        
        config.set('proxy.host', '192.168.1.1')
        config.set('proxy.port', 9090)
        config.set('scanner.timeout', 15)
        
        assert config.get('proxy.host') == '192.168.1.1'
        assert config.get('proxy.port') == 9090
        assert config.get('scanner.timeout') == 15
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_config(self, mock_json_dump, mock_file):
        """Test saving configuration to file"""
        config = Config("test_config.json")
        
        # Modify a setting
        config.set('proxy.host', '192.168.1.1')
        
        config.save_config()
        
        # Check that the file was opened for writing
        write_calls = [call for call in mock_file.call_args_list if call[0][1] == 'w']
        assert len(write_calls) >= 1
        mock_json_dump.assert_called()
    
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_save_config_error(self, mock_file):
        """Test saving configuration with error"""
        config = Config("test_config.json")
        
        # Should not raise exception
        config.save_config()
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"proxy": {"host": "192.168.1.1"}}')
    @patch('json.load')
    def test_load_config_success(self, mock_json_load, mock_file, mock_exists):
        """Test successful loading of configuration from file"""
        mock_exists.return_value = True
        mock_json_load.return_value = {"proxy": {"host": "192.168.1.1"}}
        
        config = Config("test_config.json")
        
        mock_file.assert_called_once_with("test_config.json", 'r')
        mock_json_load.assert_called_once()
        assert config.get('proxy.host') == '192.168.1.1'
    
    @patch('os.path.exists')
    def test_load_config_file_not_exists(self, mock_exists):
        """Test loading configuration when file doesn't exist"""
        mock_exists.return_value = False
        
        config = Config("test_config.json")
        
        # Should use default settings
        assert config.get('proxy.host') == '127.0.0.1'
    
    @patch('os.path.exists')
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_load_config_error(self, mock_file, mock_exists):
        """Test loading configuration with error"""
        mock_exists.return_value = True
        
        config = Config("test_config.json")
        
        # Should use default settings
        assert config.get('proxy.host') == '127.0.0.1'
    
    def test_reset_config(self):
        """Test resetting configuration to defaults"""
        config = Config("test_config.json")
        
        # Modify some settings
        config.set('proxy.host', '192.168.1.1')
        config.set('scanner.timeout', 30)
        config.set('custom.key', 'custom_value')
        
        # Reset to defaults
        config.reset()
        
        # Check that settings are back to defaults
        assert config.get('proxy.host') == '127.0.0.1'
        assert config.get('scanner.timeout') == 10
        assert config.get('custom.key') is None
    
    def test_config_merge_on_load(self):
        """Test that loaded config merges with defaults"""
        test_config = {
            "proxy": {
                "host": "192.168.1.1",
                "port": 9090
            },
            "new_section": {
                "new_key": "new_value"
            }
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
                with patch('json.load', return_value=test_config):
                    config = Config("test_config.json")
        
        # Should have loaded values
        assert config.get('proxy.host') == '192.168.1.1'
        assert config.get('proxy.port') == 9090
        assert config.get('new_section.new_key') == 'new_value'
        
        # Should still have default values for unloaded keys
        assert config.get('scanner.timeout') == 10
        assert config.get('intruder.max_threads') == 10
    
    def test_set_creates_nested_structure(self):
        """Test that set creates nested structure as needed"""
        config = Config("test_config.json")
        
        # Set a deeply nested key
        config.set('level1.level2.level3.key', 'deep_value')
        
        # Check that the structure was created
        assert config.settings['level1']['level2']['level3']['key'] == 'deep_value'
        assert config.get('level1.level2.level3.key') == 'deep_value'
    
    def test_get_with_complex_default(self):
        """Test getting key with complex default value"""
        config = Config("test_config.json")
        
        default_value = {'key': 'value', 'nested': {'inner': 'data'}}
        result = config.get('nonexistent.key', default_value)
        
        assert result == default_value
    
    def test_set_with_complex_value(self):
        """Test setting key with complex value"""
        config = Config("test_config.json")
        
        complex_value = {'key': 'value', 'nested': {'inner': 'data'}}
        config.set('complex.key', complex_value)
        
        assert config.get('complex.key') == complex_value
    
    def test_config_persistence(self):
        """Test that configuration changes persist"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # Create config and modify it
            config1 = Config(temp_file)
            config1.set('proxy.host', '192.168.1.100')
            config1.set('scanner.timeout', 25)
            
            # Create new config instance (simulates restart)
            config2 = Config(temp_file)
            
            # Check that values persisted
            assert config2.get('proxy.host') == '192.168.1.100'
            assert config2.get('scanner.timeout') == 25
        finally:
            os.unlink(temp_file)
    
    def test_invalid_key_format(self):
        """Test handling of invalid key formats"""
        config = Config("test_config.json")
        
        # Empty key
        assert config.get('') is None
        # Empty key should not crash when setting
        try:
            config.set('', 'value')
        except Exception:
            pass  # Expected to potentially fail
        
        # Key with only dots
        assert config.get('...') is None
        # Key with only dots should not crash when setting
        try:
            config.set('...', 'value')
        except Exception:
            pass  # Expected to potentially fail
    
    def test_config_file_path_handling(self):
        """Test handling of different config file paths"""
        # Test with relative path
        config1 = Config("config.json")
        assert config1.config_file == "config.json"
        
        # Test with absolute path
        config2 = Config("/tmp/burpy_config.json")
        assert config2.config_file == "/tmp/burpy_config.json"
        
        # Test with path containing directories
        config3 = Config("~/.burpy/config.json")
        assert config3.config_file == "~/.burpy/config.json"