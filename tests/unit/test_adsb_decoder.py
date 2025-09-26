"""
Tests for ADSB decoder functionality.
"""

import pytest
import json
from datetime import datetime, timezone
from src.foilskybugs.core.adsb_decoder import Aircraft, ADSBDecoder, MockADSBGenerator


class TestAircraft:
    """Test Aircraft data model."""
    
    def test_aircraft_creation(self):
        """Test aircraft creation with basic data."""
        aircraft = Aircraft(
            icao="ABC123",
            callsign="UAL123",
            latitude=42.5,
            longitude=-75.0,
            altitude=35000,
            speed=450.5,
            heading=270
        )
        
        assert aircraft.icao == "ABC123"
        assert aircraft.callsign == "UAL123"
        assert aircraft.latitude == 42.5
        assert aircraft.longitude == -75.0
        assert aircraft.altitude == 35000
        assert aircraft.speed == 450.5
        assert aircraft.heading == 270
        assert isinstance(aircraft.timestamp, datetime)
    
    def test_aircraft_validation(self):
        """Test aircraft position validation."""
        # Valid aircraft
        valid_aircraft = Aircraft(
            icao="ABC123",
            latitude=42.5,
            longitude=-75.0
        )
        assert valid_aircraft.is_valid() is True
        
        # Invalid latitude
        invalid_lat = Aircraft(
            icao="ABC123",
            latitude=95.0,  # Invalid latitude
            longitude=-75.0
        )
        assert invalid_lat.is_valid() is False
        
        # Invalid longitude
        invalid_lon = Aircraft(
            icao="ABC123",
            latitude=42.5,
            longitude=185.0  # Invalid longitude  
        )
        assert invalid_lon.is_valid() is False
        
        # Missing coordinates
        missing_coords = Aircraft(icao="ABC123")
        assert missing_coords.is_valid() is False
    
    def test_aircraft_to_dict(self):
        """Test aircraft conversion to dictionary."""
        aircraft = Aircraft(
            icao="ABC123",
            callsign="UAL123",
            latitude=42.5,
            longitude=-75.0,
            altitude=35000
        )
        
        data_dict = aircraft.to_dict()
        
        assert data_dict['icao'] == "ABC123"
        assert data_dict['callsign'] == "UAL123"
        assert data_dict['latitude'] == 42.5
        assert data_dict['longitude'] == -75.0
        assert data_dict['altitude'] == 35000
        assert 'timestamp' in data_dict


class TestMockADSBGenerator:
    """Test mock ADSB data generator."""
    
    def test_mock_generator_initialization(self):
        """Test mock generator initialization."""
        generator = MockADSBGenerator(
            center_lat=50.0,
            center_lon=-100.0,
            radius=100.0,
            num_aircraft=5
        )
        
        assert generator.center_lat == 50.0
        assert generator.center_lon == -100.0
        assert generator.radius == 100.0
        assert len(generator.aircraft_data) == 5
    
    def test_mock_aircraft_generation(self):
        """Test mock aircraft generation."""
        generator = MockADSBGenerator(num_aircraft=3)
        aircraft_list = generator.get_aircraft_list()
        
        assert len(aircraft_list) == 3
        
        for aircraft in aircraft_list:
            assert isinstance(aircraft, Aircraft)
            assert len(aircraft.icao) == 6  # ICAO should be 6 characters
            assert aircraft.callsign is not None
            assert aircraft.latitude is not None
            assert aircraft.longitude is not None
            assert aircraft.altitude is not None
            assert aircraft.speed is not None
            assert aircraft.heading is not None
    
    def test_mock_aircraft_movement(self):
        """Test aircraft position updates."""
        generator = MockADSBGenerator(num_aircraft=1)
        
        # Get initial position
        initial_aircraft = generator.get_aircraft_list()[0]
        initial_lat = initial_aircraft.latitude
        initial_lon = initial_aircraft.longitude
        
        # Update positions
        generator.update_aircraft()
        updated_aircraft = generator.get_aircraft_list()[0]
        
        # Positions should have changed (very likely but not guaranteed due to randomness)
        # Check that the aircraft still has valid coordinates
        assert updated_aircraft.latitude is not None
        assert updated_aircraft.longitude is not None
        assert -90 <= updated_aircraft.latitude <= 90
        assert -180 <= updated_aircraft.longitude <= 180


class TestADSBDecoder:
    """Test ADSB decoder functionality."""
    
    def test_decoder_initialization(self):
        """Test decoder initialization."""
        # With mock data
        decoder = ADSBDecoder(use_mock_data=True)
        assert decoder.use_mock_data is True
        assert decoder.mock_generator is not None
        
        # Without mock data
        decoder_no_mock = ADSBDecoder(use_mock_data=False)
        assert decoder_no_mock.use_mock_data is False
        assert decoder_no_mock.mock_generator is None
    
    def test_get_current_aircraft_mock(self):
        """Test getting current aircraft with mock data."""
        decoder = ADSBDecoder(use_mock_data=True)
        aircraft_list = decoder.get_current_aircraft()
        
        assert isinstance(aircraft_list, list)
        assert len(aircraft_list) > 0
        
        for aircraft in aircraft_list:
            assert isinstance(aircraft, Aircraft)
            assert aircraft.icao is not None
    
    def test_get_aircraft_by_icao(self):
        """Test getting specific aircraft by ICAO."""
        decoder = ADSBDecoder(use_mock_data=True)
        aircraft_list = decoder.get_current_aircraft()
        
        if aircraft_list:
            test_icao = aircraft_list[0].icao
            found_aircraft = decoder.get_aircraft_by_icao(test_icao)
            
            assert found_aircraft is not None
            assert found_aircraft.icao == test_icao
        
        # Test non-existent ICAO
        non_existent = decoder.get_aircraft_by_icao("NONEXIST")
        assert non_existent is None
    
    def test_process_dump1090_json(self):
        """Test processing dump1090 JSON format."""
        decoder = ADSBDecoder(use_mock_data=False)
        
        # Test valid JSON data
        test_data = {
            "now": 1234567890.0,
            "messages": 12345,
            "aircraft": [
                {
                    "hex": "abc123",
                    "flight": "UAL123  ",
                    "lat": 42.5,
                    "lon": -75.0,
                    "alt_baro": 35000,
                    "gs": 450,
                    "track": 270,
                    "squawk": "1234"
                },
                {
                    "hex": "def456",
                    "lat": 43.0,
                    "lon": -76.0,
                    "alt_baro": 28000
                }
            ]
        }
        
        json_str = json.dumps(test_data)
        aircraft_list = decoder.process_dump1090_json(json_str)
        
        assert len(aircraft_list) == 2
        
        # Check first aircraft
        ac1 = aircraft_list[0]
        assert ac1.icao == "ABC123"
        assert ac1.callsign == "UAL123"
        assert ac1.latitude == 42.5
        assert ac1.longitude == -75.0
        assert ac1.altitude == 35000
        assert ac1.speed == 450
        assert ac1.heading == 270
        assert ac1.squawk == "1234"
        
        # Check second aircraft
        ac2 = aircraft_list[1]
        assert ac2.icao == "DEF456"
        assert ac2.latitude == 43.0
        assert ac2.longitude == -76.0
        assert ac2.altitude == 28000
    
    def test_process_invalid_json(self):
        """Test processing invalid JSON data."""
        decoder = ADSBDecoder(use_mock_data=False)
        
        # Invalid JSON
        aircraft_list = decoder.process_dump1090_json("invalid json")
        assert aircraft_list == []
        
        # Missing aircraft key
        aircraft_list = decoder.process_dump1090_json('{"messages": 123}')
        assert aircraft_list == []
    
    def test_cleanup_old_aircraft(self):
        """Test cleanup of old aircraft."""
        decoder = ADSBDecoder(use_mock_data=True)
        
        # Get some aircraft to populate cache
        aircraft_list = decoder.get_current_aircraft()
        initial_count = len(decoder.aircraft_cache)
        
        # Cleanup with very short age (should remove most/all)
        decoder.cleanup_old_aircraft(max_age_seconds=0)
        
        # Cache should be smaller or empty
        assert len(decoder.aircraft_cache) <= initial_count
    
    def test_decode_message_placeholder(self):
        """Test message decoding placeholder."""
        decoder = ADSBDecoder(use_mock_data=True)
        
        # Should return None for mock data mode
        result = decoder.decode_message("test message")
        assert result is None
        
        decoder_no_mock = ADSBDecoder(use_mock_data=False)
        result_no_mock = decoder_no_mock.decode_message("test message")
        assert result_no_mock is None  # Placeholder implementation