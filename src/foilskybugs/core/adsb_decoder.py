"""
ADSB message decoder for FoilSkyBugs.

Handles decoding of ADSB messages from various sources with mock data support.
"""

import json
import random
import time
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Iterator
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Aircraft:
    """Aircraft data model."""
    icao: str
    callsign: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[int] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    vertical_rate: Optional[int] = None
    squawk: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert aircraft to dictionary."""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def is_valid(self) -> bool:
        """Check if aircraft has valid position data."""
        return (self.latitude is not None and 
                self.longitude is not None and 
                -90 <= self.latitude <= 90 and 
                -180 <= self.longitude <= 180)


class MockADSBGenerator:
    """Generate mock ADSB data for testing."""
    
    def __init__(self, center_lat: float = 42.5, center_lon: float = -75.0, 
                 radius: float = 50.0, num_aircraft: int = 10):
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.radius = radius
        self.aircraft_data = {}
        self._generate_mock_aircraft(num_aircraft)
    
    def _generate_mock_aircraft(self, num_aircraft: int):
        """Generate initial mock aircraft data."""
        airlines = ['UAL', 'DAL', 'AAL', 'SWA', 'JBU', 'VRD', 'ASA', 'FFT']
        aircraft_types = ['B737', 'A320', 'B777', 'A330', 'B787', 'A350']
        
        for i in range(num_aircraft):
            icao = f"{random.randint(0, 16777215):06X}"
            
            # Generate position within radius
            angle = random.uniform(0, 2 * 3.14159)
            distance = random.uniform(0, self.radius)
            
            # Convert to lat/lon (approximate)
            lat_offset = distance * 0.01 * math.cos(angle)
            lon_offset = distance * 0.01 * math.sin(angle)
            
            airline = random.choice(airlines)
            flight_num = random.randint(100, 9999)
            
            self.aircraft_data[icao] = Aircraft(
                icao=icao,
                callsign=f"{airline}{flight_num}",
                latitude=self.center_lat + lat_offset,
                longitude=self.center_lon + lon_offset,
                altitude=random.randint(1000, 42000),
                speed=random.randint(150, 600),
                heading=random.randint(0, 359),
                vertical_rate=random.randint(-2000, 2000),
                squawk=f"{random.randint(1000, 7777):04d}"
            )
    
    def update_aircraft(self):
        """Update aircraft positions with realistic movement."""
        for icao, aircraft in self.aircraft_data.items():
            if aircraft.latitude is None or aircraft.longitude is None:
                continue
                
            # Small random movement
            lat_change = random.uniform(-0.01, 0.01)
            lon_change = random.uniform(-0.01, 0.01)
            
            aircraft.latitude += lat_change
            aircraft.longitude += lon_change
            
            # Update other parameters
            aircraft.altitude += random.randint(-500, 500)
            aircraft.altitude = max(1000, min(42000, aircraft.altitude))
            
            aircraft.speed += random.randint(-20, 20)
            aircraft.speed = max(100, min(600, aircraft.speed))
            
            aircraft.heading = (aircraft.heading + random.randint(-10, 10)) % 360
            aircraft.timestamp = datetime.now(timezone.utc)
    
    def get_aircraft_list(self) -> List[Aircraft]:
        """Get current list of mock aircraft."""
        self.update_aircraft()
        return list(self.aircraft_data.values())


class ADSBDecoder:
    """ADSB message decoder."""
    
    def __init__(self, use_mock_data: bool = True):
        self.use_mock_data = use_mock_data
        self.mock_generator = None
        self.aircraft_cache = {}
        
        if use_mock_data:
            self.mock_generator = MockADSBGenerator()
    
    def decode_message(self, message: str) -> Optional[Aircraft]:
        """Decode a single ADSB message."""
        if self.use_mock_data:
            # For mock data, we don't actually decode messages
            return None
        
        # This would contain actual ADSB decoding logic
        # For now, return None as we're using mock data
        logger.debug(f"Would decode message: {message}")
        return None
    
    def get_current_aircraft(self) -> List[Aircraft]:
        """Get list of currently tracked aircraft."""
        if self.use_mock_data and self.mock_generator:
            aircraft_list = self.mock_generator.get_aircraft_list()
            
            # Update cache
            for aircraft in aircraft_list:
                self.aircraft_cache[aircraft.icao] = aircraft
            
            return aircraft_list
        
        # Return cached aircraft for real data
        return list(self.aircraft_cache.values())
    
    def get_aircraft_by_icao(self, icao: str) -> Optional[Aircraft]:
        """Get specific aircraft by ICAO code."""
        return self.aircraft_cache.get(icao)
    
    def process_dump1090_json(self, json_data: str) -> List[Aircraft]:
        """Process dump1090 JSON format data."""
        try:
            data = json.loads(json_data)
            aircraft_list = []
            
            for ac_data in data.get('aircraft', []):
                icao = ac_data.get('hex')
                if not icao:
                    continue
                
                aircraft = Aircraft(
                    icao=icao.upper(),
                    callsign=ac_data.get('flight', '').strip(),
                    latitude=ac_data.get('lat'),
                    longitude=ac_data.get('lon'),
                    altitude=ac_data.get('alt_baro'),
                    speed=ac_data.get('gs'),
                    heading=ac_data.get('track'),
                    vertical_rate=ac_data.get('baro_rate'),
                    squawk=ac_data.get('squawk')
                )
                
                if aircraft.is_valid():
                    aircraft_list.append(aircraft)
                    self.aircraft_cache[aircraft.icao] = aircraft
            
            return aircraft_list
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error processing dump1090 JSON: {e}")
            return []
    
    def process_beast_format(self, message: bytes) -> Optional[Aircraft]:
        """Process Beast format ADSB messages."""
        # This would contain Beast format decoding
        # For now, return None as we're focusing on JSON format
        logger.debug(f"Would process Beast message: {message.hex()}")
        return None
    
    def cleanup_old_aircraft(self, max_age_seconds: int = 300):
        """Remove aircraft that haven't been seen recently."""
        current_time = datetime.now(timezone.utc)
        to_remove = []
        
        for icao, aircraft in self.aircraft_cache.items():
            if aircraft.timestamp:
                age = (current_time - aircraft.timestamp).total_seconds()
                if age > max_age_seconds:
                    to_remove.append(icao)
        
        for icao in to_remove:
            del self.aircraft_cache[icao]
            logger.debug(f"Removed old aircraft: {icao}")