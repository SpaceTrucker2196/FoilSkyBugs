"""
Tests for database functionality.
"""

import pytest
import tempfile
import os
from datetime import datetime, timezone, timedelta

try:
    from src.foilskybugs.core.database import DatabaseManager, AircraftPosition, Statistics
    from src.foilskybugs.core.config import DatabaseConfig
    from src.foilskybugs.core.adsb_decoder import Aircraft
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False


@pytest.mark.skipif(not HAS_DATABASE, reason="SQLAlchemy not available")
class TestDatabaseManager:
    """Test database manager functionality."""
    
    @pytest.fixture
    def temp_db_config(self):
        """Create temporary database configuration."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        config = DatabaseConfig(
            url=f"sqlite:///{temp_db.name}",
            retention_positions=7,
            retention_statistics=30
        )
        
        yield config
        
        # Cleanup
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)
    
    @pytest.fixture
    def db_manager(self, temp_db_config):
        """Create database manager with temporary database."""
        return DatabaseManager(temp_db_config)
    
    def test_database_initialization(self, db_manager):
        """Test database initialization."""
        assert db_manager.engine is not None
        assert db_manager.SessionLocal is not None
        
        # Test health check
        assert db_manager.health_check() is True
    
    def test_store_aircraft_position(self, db_manager):
        """Test storing single aircraft position."""
        aircraft = Aircraft(
            icao="ABC123",
            callsign="UAL123",
            latitude=42.5,
            longitude=-75.0,
            altitude=35000,
            speed=450,
            heading=270,
            squawk="1234"
        )
        
        success = db_manager.store_aircraft_position(aircraft)
        assert success is True
        
        # Verify data was stored
        positions = db_manager.get_aircraft_positions(icao="ABC123", limit=1)
        assert len(positions) == 1
        
        stored_position = positions[0]
        assert stored_position['icao'] == "ABC123"
        assert stored_position['callsign'] == "UAL123"
        assert stored_position['latitude'] == 42.5
        assert stored_position['longitude'] == -75.0
        assert stored_position['altitude'] == 35000
        assert stored_position['speed'] == 450
        assert stored_position['heading'] == 270
        assert stored_position['squawk'] == "1234"
    
    def test_store_multiple_aircraft_positions(self, db_manager):
        """Test storing multiple aircraft positions."""
        aircraft_list = [
            Aircraft(
                icao="ABC123",
                callsign="UAL123",
                latitude=42.5,
                longitude=-75.0,
                altitude=35000
            ),
            Aircraft(
                icao="DEF456",
                callsign="DAL456", 
                latitude=43.0,
                longitude=-76.0,
                altitude=28000
            ),
            Aircraft(
                icao="INVALID",  # Invalid aircraft (no valid position)
                latitude=None,
                longitude=None
            )
        ]
        
        stored_count = db_manager.store_aircraft_positions(aircraft_list)
        assert stored_count == 2  # Only 2 valid aircraft should be stored
        
        # Verify data
        positions = db_manager.get_aircraft_positions(limit=10)
        assert len(positions) == 2
        
        icaos = {pos['icao'] for pos in positions}
        assert "ABC123" in icaos
        assert "DEF456" in icaos
        assert "INVALID" not in icaos
    
    def test_get_aircraft_positions_filtering(self, db_manager):
        """Test getting aircraft positions with filtering."""
        # Store test data with different timestamps
        now = datetime.now(timezone.utc)
        old_time = now - timedelta(hours=2)
        
        aircraft_old = Aircraft(
            icao="OLD123",
            latitude=42.0,
            longitude=-75.0,
            timestamp=old_time
        )
        
        aircraft_new = Aircraft(
            icao="NEW456",
            latitude=43.0,
            longitude=-76.0,
            timestamp=now
        )
        
        db_manager.store_aircraft_position(aircraft_old)
        db_manager.store_aircraft_position(aircraft_new)
        
        # Test ICAO filtering
        old_positions = db_manager.get_aircraft_positions(icao="OLD123")
        assert len(old_positions) == 1
        assert old_positions[0]['icao'] == "OLD123"
        
        # Test time filtering
        recent_positions = db_manager.get_aircraft_positions(
            start_time=now - timedelta(minutes=30)
        )
        assert len(recent_positions) == 1
        assert recent_positions[0]['icao'] == "NEW456"
        
        # Test limit
        limited_positions = db_manager.get_aircraft_positions(limit=1)
        assert len(limited_positions) == 1
    
    def test_get_current_aircraft(self, db_manager):
        """Test getting current aircraft."""
        now = datetime.now(timezone.utc)
        old_time = now - timedelta(minutes=10)  # Too old
        recent_time = now - timedelta(minutes=2)  # Recent enough
        
        # Store old aircraft (should not appear in current)
        old_aircraft = Aircraft(
            icao="OLD123",
            latitude=42.0,
            longitude=-75.0,
            timestamp=old_time
        )
        db_manager.store_aircraft_position(old_aircraft)
        
        # Store recent aircraft (should appear in current)
        recent_aircraft = Aircraft(
            icao="RECENT456",
            latitude=43.0,
            longitude=-76.0,
            timestamp=recent_time
        )
        db_manager.store_aircraft_position(recent_aircraft)
        
        current_aircraft = db_manager.get_current_aircraft(max_age_minutes=5)
        
        # Should only contain recent aircraft
        assert len(current_aircraft) == 1
        assert current_aircraft[0]['icao'] == "RECENT456"
    
    def test_update_statistics(self, db_manager):
        """Test statistics update."""
        # Store some test data
        aircraft_list = [
            Aircraft(icao="ABC123", callsign="UAL123", altitude=35000),
            Aircraft(icao="DEF456", callsign="DAL456", altitude=28000),
            Aircraft(icao="ABC123", callsign="UAL123", altitude=36000),  # Same aircraft, different position
        ]
        
        for aircraft in aircraft_list:
            db_manager.store_aircraft_position(aircraft)
        
        # Update statistics
        success = db_manager.update_statistics()
        assert success is True
        
        # Verify statistics
        stats = db_manager.get_statistics(days=1)
        assert len(stats) == 1
        
        today_stats = stats[0]
        assert today_stats['total_aircraft'] == 2  # Unique aircraft
        assert today_stats['total_positions'] == 3
        assert today_stats['unique_callsigns'] == 2
        assert today_stats['max_altitude'] == 36000
        # Average of 35000, 28000, 36000 = 33000
        assert 32500 <= today_stats['avg_altitude'] <= 33500
    
    def test_cleanup_old_data(self, db_manager):
        """Test cleanup of old data."""
        # Store old position data
        old_time = datetime.now(timezone.utc) - timedelta(days=40)
        old_aircraft = Aircraft(
            icao="OLD123",
            latitude=42.0,
            longitude=-75.0,
            timestamp=old_time
        )
        db_manager.store_aircraft_position(old_aircraft)
        
        # Store recent data
        recent_aircraft = Aircraft(
            icao="RECENT456",
            latitude=43.0,
            longitude=-76.0
        )
        db_manager.store_aircraft_position(recent_aircraft)
        
        # Verify both exist before cleanup
        all_positions = db_manager.get_aircraft_positions(limit=10)
        assert len(all_positions) == 2
        
        # Run cleanup (should remove positions older than retention_positions days)
        success = db_manager.cleanup_old_data()
        assert success is True
        
        # Verify old data was removed
        remaining_positions = db_manager.get_aircraft_positions(limit=10)
        assert len(remaining_positions) == 1
        assert remaining_positions[0]['icao'] == "RECENT456"
    
    def test_health_check(self, db_manager):
        """Test database health check."""
        assert db_manager.health_check() is True
    
    def test_invalid_database_url(self):
        """Test handling of invalid database URL."""
        invalid_config = DatabaseConfig(url="invalid://url")
        
        with pytest.raises(Exception):
            DatabaseManager(invalid_config)