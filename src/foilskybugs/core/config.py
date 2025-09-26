"""
Configuration management for FoilSkyBugs.

Handles loading and parsing YAML configuration files with defaults.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class DataSourceConfig:
    """Configuration for ADSB data sources."""
    enabled: bool = True
    host: str = "localhost"
    port: int = 30003
    format: str = "beast"
    name: str = "dump1090"


@dataclass
class RTLSDRConfig:
    """Configuration for RTL-SDR hardware."""
    enabled: bool = False
    device_index: int = 0
    frequency: int = 1090000000
    sample_rate: int = 2000000
    gain: str = "auto"


@dataclass
class GeographicConfig:
    """Geographic filtering configuration."""
    center_lat: float = 42.5
    center_lon: float = -75.0
    max_range: float = 250.0
    bounds_north: float = 45.0
    bounds_south: float = 40.0
    bounds_east: float = -70.0
    bounds_west: float = -80.0


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = "sqlite:///foilskybugs.db"
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    retention_positions: int = 30
    retention_tracks: int = 90
    retention_statistics: int = 365


@dataclass
class WebConfig:
    """Web interface configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    secret_key: str = "dev-secret-key-change-in-production"


@dataclass
class Config:
    """Main configuration class for FoilSkyBugs."""
    app_name: str = "FoilSkyBugs"
    app_version: str = "1.0.0"
    environment: str = "development"
    
    # Component configurations
    data_sources: List[DataSourceConfig] = field(default_factory=list)
    rtl_sdr: RTLSDRConfig = field(default_factory=RTLSDRConfig)
    geographic: GeographicConfig = field(default_factory=GeographicConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    web: WebConfig = field(default_factory=WebConfig)
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "foilskybugs.log"
    
    @classmethod
    def from_file(cls, config_path: str) -> 'Config':
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            print(f"Warning: Config file {config_path} not found, using defaults")
            return cls()
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return cls.from_dict(config_data)
    
    @classmethod
    def from_dict(cls, config_data: Dict[str, Any]) -> 'Config':
        """Create configuration from dictionary."""
        config = cls()
        
        # App configuration
        app_config = config_data.get('app', {})
        config.app_name = app_config.get('name', config.app_name)
        config.app_version = app_config.get('version', config.app_version)
        config.environment = app_config.get('environment', config.environment)
        
        # Data sources
        data_sources_config = config_data.get('data_sources', {})
        network_feeds = data_sources_config.get('network_feeds', [])
        config.data_sources = [
            DataSourceConfig(
                enabled=feed.get('enabled', True),
                host=feed.get('host', 'localhost'),
                port=feed.get('port', 30003),
                format=feed.get('format', 'beast'),
                name=feed.get('name', 'dump1090')
            )
            for feed in network_feeds
        ]
        
        # RTL-SDR
        rtl_config = data_sources_config.get('rtl_sdr', {})
        config.rtl_sdr = RTLSDRConfig(
            enabled=rtl_config.get('enabled', False),
            device_index=rtl_config.get('device_index', 0),
            frequency=rtl_config.get('frequency', 1090000000),
            sample_rate=rtl_config.get('sample_rate', 2000000),
            gain=rtl_config.get('gain', 'auto')
        )
        
        # Geographic
        geo_config = config_data.get('geographic', {})
        bounds = geo_config.get('bounds', {})
        center = geo_config.get('center', {})
        config.geographic = GeographicConfig(
            center_lat=center.get('latitude', 42.5),
            center_lon=center.get('longitude', -75.0),
            max_range=geo_config.get('max_range', 250.0),
            bounds_north=bounds.get('north', 45.0),
            bounds_south=bounds.get('south', 40.0),
            bounds_east=bounds.get('east', -70.0),
            bounds_west=bounds.get('west', -80.0)
        )
        
        # Database
        db_config = config_data.get('database', {})
        retention = db_config.get('retention', {})
        config.database = DatabaseConfig(
            url=db_config.get('url', 'sqlite:///foilskybugs.db'),
            pool_size=db_config.get('pool_size', 20),
            max_overflow=db_config.get('max_overflow', 30),
            pool_timeout=db_config.get('pool_timeout', 30),
            pool_recycle=db_config.get('pool_recycle', 3600),
            retention_positions=retention.get('positions', 30),
            retention_tracks=retention.get('tracks', 90),
            retention_statistics=retention.get('statistics', 365)
        )
        
        # Web
        web_config = config_data.get('web', {})
        config.web = WebConfig(
            host=web_config.get('host', '0.0.0.0'),
            port=web_config.get('port', 8080),
            debug=web_config.get('debug', False),
            secret_key=web_config.get('secret_key', 'dev-secret-key-change-in-production')
        )
        
        # Logging
        logging_config = config_data.get('logging', {})
        config.log_level = logging_config.get('level', 'INFO')
        config.log_file = logging_config.get('file', 'foilskybugs.log')
        
        return config
    
    def get_default_data_source(self) -> Optional[DataSourceConfig]:
        """Get the first enabled data source."""
        for source in self.data_sources:
            if source.enabled:
                return source
        return None