"""
Data utility functions for FoilSkyBugs.
"""

import re
from datetime import datetime, timezone
from typing import Optional


def format_timestamp(timestamp: datetime) -> str:
    """
    Format timestamp for display.
    
    Args:
        timestamp: DateTime object
        
    Returns:
        Formatted timestamp string
    """
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")


def clean_callsign(callsign: Optional[str]) -> Optional[str]:
    """
    Clean and validate aircraft callsign.
    
    Args:
        callsign: Raw callsign string
        
    Returns:
        Cleaned callsign or None if invalid
    """
    if not callsign:
        return None
    
    # Remove whitespace and convert to uppercase
    callsign = callsign.strip().upper()
    
    if not callsign:
        return None
    
    # Remove non-alphanumeric characters except hyphens
    callsign = re.sub(r'[^A-Z0-9-]', '', callsign)
    
    # Validate length (typically 2-8 characters)
    if len(callsign) < 2 or len(callsign) > 8:
        return None
    
    return callsign


def validate_icao(icao: Optional[str]) -> bool:
    """
    Validate ICAO aircraft identifier.
    
    Args:
        icao: ICAO identifier string
        
    Returns:
        True if valid, False otherwise
    """
    if not icao:
        return False
    
    icao = icao.strip().upper()
    
    # ICAO should be exactly 6 hexadecimal characters
    if len(icao) != 6:
        return False
    
    # Check if all characters are valid hex
    try:
        int(icao, 16)
        return True
    except ValueError:
        return False


def validate_squawk(squawk: Optional[str]) -> bool:
    """
    Validate aircraft squawk code.
    
    Args:
        squawk: Squawk code string
        
    Returns:
        True if valid, False otherwise
    """
    if not squawk:
        return False
    
    squawk = squawk.strip()
    
    # Squawk should be exactly 4 octal digits (0-7)
    if len(squawk) != 4:
        return False
    
    # Check if all characters are valid octal digits
    return all(c in '01234567' for c in squawk)


def validate_altitude(altitude: Optional[int]) -> bool:
    """
    Validate aircraft altitude.
    
    Args:
        altitude: Altitude in feet
        
    Returns:
        True if valid, False otherwise
    """
    if altitude is None:
        return False
    
    # Reasonable altitude range for commercial aircraft
    return -1000 <= altitude <= 60000


def validate_speed(speed: Optional[float]) -> bool:
    """
    Validate aircraft ground speed.
    
    Args:
        speed: Ground speed in knots
        
    Returns:
        True if valid, False otherwise
    """
    if speed is None:
        return False
    
    # Reasonable speed range
    return 0 <= speed <= 1000


def validate_heading(heading: Optional[float]) -> bool:
    """
    Validate aircraft heading.
    
    Args:
        heading: Heading in degrees
        
    Returns:
        True if valid, False otherwise
    """
    if heading is None:
        return False
    
    return 0 <= heading < 360


def normalize_icao(icao: str) -> str:
    """
    Normalize ICAO identifier to standard format.
    
    Args:
        icao: Raw ICAO identifier
        
    Returns:
        Normalized ICAO identifier (6 uppercase hex chars)
    """
    if not icao:
        return ""
    
    icao = icao.strip().upper()
    
    # Pad with leading zeros if necessary
    if len(icao) < 6 and validate_icao('0' * (6 - len(icao)) + icao):
        icao = '0' * (6 - len(icao)) + icao
    
    return icao if validate_icao(icao) else ""


def parse_aircraft_type(icao: str) -> Optional[str]:
    """
    Attempt to determine aircraft type from ICAO identifier.
    
    This is a simplified implementation - in reality, you'd need
    a database of ICAO allocations.
    
    Args:
        icao: ICAO identifier
        
    Returns:
        Aircraft type guess or None
    """
    if not validate_icao(icao):
        return None
    
    # This is a very basic implementation
    # In practice, you'd use a proper ICAO database
    first_byte = int(icao[:2], 16)
    
    if 0xA0 <= first_byte <= 0xA7:
        return "US Registered"
    elif 0x40 <= first_byte <= 0x47:
        return "UK Registered"
    elif 0x38 <= first_byte <= 0x3F:
        return "German Registered"
    elif 0x48 <= first_byte <= 0x4F:
        return "Netherlands Registered"
    
    return "Unknown"


def format_flight_level(altitude: Optional[int]) -> str:
    """
    Format altitude as flight level when appropriate.
    
    Args:
        altitude: Altitude in feet
        
    Returns:
        Formatted altitude/flight level string
    """
    if altitude is None:
        return "N/A"
    
    if altitude >= 18000:
        # Flight levels (divide by 100)
        fl = altitude // 100
        return f"FL{fl:03d}"
    else:
        return f"{altitude:,}ft"