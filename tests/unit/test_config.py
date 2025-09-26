"""
Tests for configuration management.
"""

import pytest
import tempfile
import os
import yaml
from src.foilskybugs.core.config import Config, DataSourceConfig, DatabaseConfig


class TestConfig:
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = Config()
        
        assert config.app_name == "FoilSkyBugs"
        assert config.app_version == "1.0.0"
        assert config.environment == "development"
        assert config.log_level == "INFO"
        assert config.database.url == "sqlite:///foilskybugs.db"
        assert config.web.port == 8080
    
    def test_config_from_dict(self):
        """Test configuration from dictionary."""
        config_data = {
            'app': {
                'name': 'TestApp',
                'version': '2.0.0',
                'environment': 'production'
            },
            'database': {
                'url': 'postgresql://test:test@localhost/test',
                'pool_size': 10
            },
            'web': {
                'port': 9090,
                'host': '127.0.0.1'
            }
        }
        
        config = Config.from_dict(config_data)
        
        assert config.app_name == "TestApp"
        assert config.app_version == "2.0.0"
        assert config.environment == "production"
        assert config.database.url == "postgresql://test:test@localhost/test"
        assert config.database.pool_size == 10
        assert config.web.port == 9090
        assert config.web.host == "127.0.0.1"
    
    def test_config_from_file(self):
        """Test configuration from YAML file."""
        config_data = {
            'app': {
                'name': 'FileTestApp',
                'version': '3.0.0'
            },
            'data_sources': {
                'network_feeds': [
                    {
                        'name': 'test_feed',
                        'host': 'test.example.com',
                        'port': 12345,
                        'enabled': True
                    }
                ]
            },
            'geographic': {
                'center': {
                    'latitude': 50.0,
                    'longitude': -100.0
                },
                'bounds': {
                    'north': 55.0,
                    'south': 45.0,
                    'east': -95.0,
                    'west': -105.0
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name
        
        try:
            config = Config.from_file(temp_file)
            
            assert config.app_name == "FileTestApp"
            assert config.app_version == "3.0.0"
            assert len(config.data_sources) == 1
            assert config.data_sources[0].name == "test_feed"
            assert config.data_sources[0].host == "test.example.com"
            assert config.data_sources[0].port == 12345
            assert config.geographic.center_lat == 50.0
            assert config.geographic.center_lon == -100.0
            
        finally:
            os.unlink(temp_file)
    
    def test_config_from_nonexistent_file(self):
        """Test configuration from non-existent file."""
        config = Config.from_file('/path/that/does/not/exist.yaml')
        
        # Should return default configuration
        assert config.app_name == "FoilSkyBugs"
        assert config.app_version == "1.0.0"
    
    def test_data_source_config(self):
        """Test data source configuration."""
        ds_config = DataSourceConfig(
            name="test_source",
            host="192.168.1.100",
            port=30003,
            format="beast",
            enabled=True
        )
        
        assert ds_config.name == "test_source"
        assert ds_config.host == "192.168.1.100"
        assert ds_config.port == 30003
        assert ds_config.format == "beast"
        assert ds_config.enabled is True
    
    def test_database_config(self):
        """Test database configuration."""
        db_config = DatabaseConfig(
            url="postgresql://user:pass@host:5432/db",
            pool_size=15,
            retention_positions=45
        )
        
        assert db_config.url == "postgresql://user:pass@host:5432/db"
        assert db_config.pool_size == 15
        assert db_config.retention_positions == 45
        assert db_config.max_overflow == 30  # default value
    
    def test_get_default_data_source(self):
        """Test getting default data source."""
        config = Config()
        
        # No data sources configured
        assert config.get_default_data_source() is None
        
        # Add some data sources
        config.data_sources = [
            DataSourceConfig(name="disabled", enabled=False),
            DataSourceConfig(name="enabled1", enabled=True),
            DataSourceConfig(name="enabled2", enabled=True)
        ]
        
        # Should return first enabled source
        default_source = config.get_default_data_source()
        assert default_source is not None
        assert default_source.name == "enabled1"
        assert default_source.enabled is True