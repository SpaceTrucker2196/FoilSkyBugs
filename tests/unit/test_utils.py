"""
Tests for utility functions.
"""

import pytest
from datetime import datetime, timezone

from src.foilskybugs.utils.geo_utils import (
    calculate_distance, validate_coordinates, within_bounds, 
    calculate_bearing, nm_to_km, km_to_nm, feet_to_meters, meters_to_feet
)
from src.foilskybugs.utils.data_utils import (
    format_timestamp, clean_callsign, validate_icao, validate_squawk,
    validate_altitude, validate_speed, validate_heading, normalize_icao,
    parse_aircraft_type, format_flight_level
)


class TestGeoUtils:
    """Test geographic utility functions."""
    
    def test_calculate_distance(self):
        """Test distance calculation."""
        # Distance from New York to London (approximately 3000 nm)
        nyc_lat, nyc_lon = 40.7128, -74.0060
        london_lat, london_lon = 51.5074, -0.1278
        
        distance = calculate_distance(nyc_lat, nyc_lon, london_lat, london_lon)
        
        # Should be approximately 3000 nautical miles
        assert 2900 <= distance <= 3100
    
    def test_calculate_distance_same_point(self):
        """Test distance calculation for same point."""
        lat, lon = 42.5, -75.0
        distance = calculate_distance(lat, lon, lat, lon)
        assert distance == pytest.approx(0, abs=0.01)
    
    def test_validate_coordinates(self):
        """Test coordinate validation."""
        # Valid coordinates
        assert validate_coordinates(42.5, -75.0) is True
        assert validate_coordinates(0, 0) is True
        assert validate_coordinates(90, 180) is True
        assert validate_coordinates(-90, -180) is True
        
        # Invalid coordinates
        assert validate_coordinates(95, -75.0) is False  # Invalid latitude
        assert validate_coordinates(42.5, 185) is False  # Invalid longitude
        assert validate_coordinates(None, -75.0) is False  # None latitude
        assert validate_coordinates(42.5, None) is False  # None longitude
    
    def test_within_bounds(self):
        """Test bounds checking."""
        # Point within bounds
        assert within_bounds(42.5, -75.0, 45.0, 40.0, -70.0, -80.0) is True
        
        # Point outside bounds
        assert within_bounds(47.0, -75.0, 45.0, 40.0, -70.0, -80.0) is False  # North of bounds
        assert within_bounds(42.5, -65.0, 45.0, 40.0, -70.0, -80.0) is False  # East of bounds
        
        # Invalid coordinates
        assert within_bounds(95.0, -75.0, 45.0, 40.0, -70.0, -80.0) is False
    
    def test_calculate_bearing(self):
        """Test bearing calculation."""
        # North bearing
        bearing = calculate_bearing(0, 0, 1, 0)
        assert bearing == pytest.approx(0, abs=1)
        
        # East bearing
        bearing = calculate_bearing(0, 0, 0, 1)
        assert bearing == pytest.approx(90, abs=1)
        
        # South bearing
        bearing = calculate_bearing(0, 0, -1, 0)
        assert bearing == pytest.approx(180, abs=1)
        
        # West bearing
        bearing = calculate_bearing(0, 0, 0, -1)
        assert bearing == pytest.approx(270, abs=1)
    
    def test_unit_conversions(self):
        """Test unit conversion functions."""
        # Nautical miles to kilometers
        assert nm_to_km(1) == pytest.approx(1.852, abs=0.001)
        assert nm_to_km(10) == pytest.approx(18.52, abs=0.01)
        
        # Kilometers to nautical miles
        assert km_to_nm(1.852) == pytest.approx(1, abs=0.001)
        assert km_to_nm(18.52) == pytest.approx(10, abs=0.01)
        
        # Feet to meters
        assert feet_to_meters(1) == pytest.approx(0.3048, abs=0.0001)
        assert feet_to_meters(1000) == pytest.approx(304.8, abs=0.1)
        
        # Meters to feet
        assert meters_to_feet(1) == pytest.approx(3.28084, abs=0.001)
        assert meters_to_feet(100) == pytest.approx(328.084, abs=0.01)


class TestDataUtils:
    """Test data utility functions."""
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        # UTC timestamp
        timestamp = datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        formatted = format_timestamp(timestamp)
        assert formatted == "2024-01-15 12:30:45 UTC"
        
        # Naive timestamp (should be treated as UTC)
        naive_timestamp = datetime(2024, 1, 15, 12, 30, 45)
        formatted = format_timestamp(naive_timestamp)
        assert formatted == "2024-01-15 12:30:45 UTC"
    
    def test_clean_callsign(self):
        """Test callsign cleaning."""
        # Valid callsigns
        assert clean_callsign("UAL123") == "UAL123"
        assert clean_callsign("  dal456  ") == "DAL456"
        assert clean_callsign("SWA-789") == "SWA-789"
        
        # Invalid callsigns
        assert clean_callsign("") is None
        assert clean_callsign("   ") is None
        assert clean_callsign(None) is None
        assert clean_callsign("A") is None  # Too short
        assert clean_callsign("VERYLONGCALLSIGN") is None  # Too long
        
        # Callsign with invalid characters
        assert clean_callsign("UAL123!@#") == "UAL123"
    
    def test_validate_icao(self):
        """Test ICAO validation."""
        # Valid ICAOs
        assert validate_icao("ABC123") is True
        assert validate_icao("123ABC") is True
        assert validate_icao("000000") is True
        assert validate_icao("FFFFFF") is True
        
        # Invalid ICAOs
        assert validate_icao("") is False
        assert validate_icao(None) is False
        assert validate_icao("ABC12") is False  # Too short
        assert validate_icao("ABC1234") is False  # Too long
        assert validate_icao("ABCXYZ") is False  # Invalid hex characters
        assert validate_icao("ABC12G") is False  # Invalid hex character
    
    def test_validate_squawk(self):
        """Test squawk code validation."""
        # Valid squawks
        assert validate_squawk("1234") is True
        assert validate_squawk("0000") is True
        assert validate_squawk("7777") is True
        
        # Invalid squawks
        assert validate_squawk("") is False
        assert validate_squawk(None) is False
        assert validate_squawk("123") is False  # Too short
        assert validate_squawk("12345") is False  # Too long
        assert validate_squawk("1238") is False  # Invalid octal digit
        assert validate_squawk("123A") is False  # Non-digit
    
    def test_validate_altitude(self):
        """Test altitude validation."""
        # Valid altitudes
        assert validate_altitude(0) is True
        assert validate_altitude(35000) is True
        assert validate_altitude(-500) is True  # Below sea level
        
        # Invalid altitudes
        assert validate_altitude(None) is False
        assert validate_altitude(-2000) is False  # Too low
        assert validate_altitude(70000) is False  # Too high
    
    def test_validate_speed(self):
        """Test speed validation."""
        # Valid speeds
        assert validate_speed(0) is True
        assert validate_speed(450.5) is True
        assert validate_speed(999) is True
        
        # Invalid speeds
        assert validate_speed(None) is False
        assert validate_speed(-10) is False  # Negative speed
        assert validate_speed(1001) is False  # Too fast
    
    def test_validate_heading(self):
        """Test heading validation."""
        # Valid headings
        assert validate_heading(0) is True
        assert validate_heading(180.5) is True
        assert validate_heading(359) is True
        
        # Invalid headings
        assert validate_heading(None) is False
        assert validate_heading(-1) is False  # Negative
        assert validate_heading(360) is False  # Too high
        assert validate_heading(370) is False  # Way too high
    
    def test_normalize_icao(self):
        """Test ICAO normalization."""
        # Already valid
        assert normalize_icao("ABC123") == "ABC123"
        
        # Needs padding
        assert normalize_icao("ABC12") == "0ABC12"
        assert normalize_icao("A1") == "0000A1"
        
        # Needs cleaning
        assert normalize_icao("  abc123  ") == "ABC123"
        
        # Invalid ICAO
        assert normalize_icao("INVALID") == ""
        assert normalize_icao("") == ""
    
    def test_parse_aircraft_type(self):
        """Test aircraft type parsing."""
        # US registered (A0-A7)
        assert parse_aircraft_type("A12345") == "US Registered"
        
        # UK registered (40-47)
        assert parse_aircraft_type("412345") == "UK Registered"
        
        # German registered (38-3F)
        assert parse_aircraft_type("3A2345") == "German Registered"
        
        # Netherlands registered (48-4F)
        assert parse_aircraft_type("4A2345") == "Netherlands Registered"
        
        # Unknown
        assert parse_aircraft_type("123456") == "Unknown"
        
        # Invalid ICAO
        assert parse_aircraft_type("INVALID") is None
    
    def test_format_flight_level(self):
        """Test flight level formatting."""
        # Flight levels (18,000+ feet)
        assert format_flight_level(18000) == "FL180"
        assert format_flight_level(35000) == "FL350"
        assert format_flight_level(41000) == "FL410"
        
        # Regular altitudes (below 18,000 feet)
        assert format_flight_level(5000) == "5,000ft"
        assert format_flight_level(12500) == "12,500ft"
        
        # None altitude
        assert format_flight_level(None) == "N/A"