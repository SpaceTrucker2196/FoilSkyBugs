"""
Integration tests for the full FoilSkyBugs system.
"""

import pytest
import tempfile
import os
import time
import threading
from datetime import datetime, timezone

from src.foilskybugs.core.config import Config, DatabaseConfig
from src.foilskybugs.core.foilskybugs import FoilSkyBugs


class TestFullSystem:
    """Test the full system integration."""
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary configuration for testing."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        config = Config()
        config.database = DatabaseConfig(url=f"sqlite:///{temp_db.name}")
        config.log_file = tempfile.mktemp(suffix='.log')
        
        yield config
        
        # Cleanup
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)
        if os.path.exists(config.log_file):
            os.unlink(config.log_file)
    
    def test_system_initialization(self, temp_config):
        """Test full system initialization."""
        app = FoilSkyBugs(temp_config)
        
        # Check components are initialized
        assert app.config == temp_config
        assert app.decoder is not None
        assert app.database is not None
        assert app.running is False
    
    def test_start_stop_cycle(self, temp_config):
        """Test starting and stopping the system."""
        app = FoilSkyBugs(temp_config)
        
        # Start the system
        assert app.start() is True
        assert app.running is True
        assert app.data_thread is not None
        assert app.data_thread.is_alive()
        
        # Let it run briefly
        time.sleep(2)
        
        # Stop the system
        assert app.stop() is True
        assert app.running is False
        
        # Wait for thread to finish
        time.sleep(1)
        assert not app.data_thread.is_alive()
    
    def test_data_collection_and_storage(self, temp_config):
        """Test data collection and database storage."""
        app = FoilSkyBugs(temp_config)
        
        # Start data collection
        app.start()
        
        # Wait for some data to be collected and stored
        time.sleep(3)
        
        # Check that aircraft data is available
        current_aircraft = app.get_current_aircraft()
        assert len(current_aircraft) > 0
        
        # Check that data was stored in database
        db_aircraft = app.database.get_current_aircraft()
        assert len(db_aircraft) > 0
        
        # Verify structure of aircraft data
        aircraft = current_aircraft[0]
        assert 'icao' in aircraft
        assert 'latitude' in aircraft
        assert 'longitude' in aircraft
        assert 'timestamp' in aircraft
        
        app.stop()
    
    def test_health_check(self, temp_config):
        """Test system health check."""
        app = FoilSkyBugs(temp_config)
        
        health = app.health_check()
        
        assert 'status' in health
        assert 'timestamp' in health
        assert 'components' in health
        
        # Check component statuses
        components = health['components']
        assert 'database' in components
        assert 'data_collection' in components
        assert 'decoder' in components
        
        # Database should be healthy
        assert components['database']['status'] == 'healthy'
        
        # Data collection should be stopped initially
        assert components['data_collection']['status'] == 'stopped'
        
        # Decoder should be healthy
        assert components['decoder']['status'] == 'healthy'
    
    def test_data_persistence(self, temp_config):
        """Test that data persists between sessions."""
        # First session - collect some data
        app1 = FoilSkyBugs(temp_config)
        app1.start()
        time.sleep(2)
        
        # Get some aircraft data
        aircraft_before = app1.get_current_aircraft()
        assert len(aircraft_before) > 0
        
        app1.stop()
        
        # Second session - check data is still there
        app2 = FoilSkyBugs(temp_config)
        
        # Check database still has data
        db_aircraft = app2.database.get_aircraft_positions(limit=100)
        assert len(db_aircraft) > 0
        
        # Verify data integrity
        for aircraft in db_aircraft:
            assert aircraft['icao'] is not None
            assert aircraft['timestamp'] is not None
    
    def test_export_functionality(self, temp_config):
        """Test data export functionality."""
        app = FoilSkyBugs(temp_config)
        
        # Start and collect some data
        app.start()
        time.sleep(2)
        app.stop()
        
        # Test JSON export
        temp_json = tempfile.mktemp(suffix='.json')
        success = app.export_data(format='json', output_file=temp_json)
        
        if success:
            assert os.path.exists(temp_json)
            # Verify file has content
            assert os.path.getsize(temp_json) > 0
            os.unlink(temp_json)
        
        # Test CSV export
        temp_csv = tempfile.mktemp(suffix='.csv')
        success = app.export_data(format='csv', output_file=temp_csv)
        
        if success:
            assert os.path.exists(temp_csv)
            os.unlink(temp_csv)
        
        # Test GeoJSON export
        temp_geojson = tempfile.mktemp(suffix='.geojson')
        success = app.export_data(format='geojson', output_file=temp_geojson)
        
        if success:
            assert os.path.exists(temp_geojson)
            os.unlink(temp_geojson)
    
    def test_aircraft_tracking(self, temp_config):
        """Test aircraft tracking functionality."""
        app = FoilSkyBugs(temp_config)
        app.start()
        time.sleep(2)
        
        # Get current aircraft
        aircraft_list = app.get_current_aircraft()
        assert len(aircraft_list) > 0
        
        # Pick an aircraft to track
        test_aircraft = aircraft_list[0]
        test_icao = test_aircraft['icao']
        
        # Get specific aircraft
        specific_aircraft = app.get_aircraft_by_icao(test_icao)
        assert specific_aircraft is not None
        assert specific_aircraft['icao'] == test_icao
        
        # Wait a bit more for history
        time.sleep(2)
        
        # Get aircraft history
        history = app.get_aircraft_history(test_icao, hours=1)
        assert len(history) >= 1
        
        app.stop()
    
    def test_concurrent_access(self, temp_config):
        """Test concurrent access to the system."""
        app = FoilSkyBugs(temp_config)
        app.start()
        
        results = []
        
        def get_aircraft_data():
            """Worker function to get aircraft data."""
            try:
                aircraft = app.get_current_aircraft()
                results.append(len(aircraft))
            except Exception as e:
                results.append(f"Error: {e}")
        
        # Create multiple threads accessing data simultaneously
        threads = []
        for _ in range(5):
            t = threading.Thread(target=get_aircraft_data)
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        app.stop()
        
        # Check that all threads got data successfully
        assert len(results) == 5
        for result in results:
            assert isinstance(result, int)  # Should be aircraft count, not error
            assert result >= 0