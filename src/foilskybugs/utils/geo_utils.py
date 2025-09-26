"""
Geographic utility functions for FoilSkyBugs.
"""

import math
from typing import Tuple, Optional


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.
    
    Args:
        lat1, lon1: Latitude and longitude of first point in decimal degrees
        lat2, lon2: Latitude and longitude of second point in decimal degrees
        
    Returns:
        Distance in nautical miles
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = (math.sin(dlat/2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # Earth's radius in nautical miles
    earth_radius_nm = 3440.065
    
    return earth_radius_nm * c


def validate_coordinates(latitude: Optional[float], longitude: Optional[float]) -> bool:
    """
    Validate latitude and longitude coordinates.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        True if coordinates are valid, False otherwise
    """
    if latitude is None or longitude is None:
        return False
    
    return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)


def within_bounds(latitude: float, longitude: float, 
                 north: float, south: float, east: float, west: float) -> bool:
    """
    Check if coordinates are within given bounds.
    
    Args:
        latitude, longitude: Point coordinates
        north, south, east, west: Bounding box coordinates
        
    Returns:
        True if point is within bounds, False otherwise
    """
    if not validate_coordinates(latitude, longitude):
        return False
    
    return (south <= latitude <= north) and (west <= longitude <= east)


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate bearing from point 1 to point 2.
    
    Args:
        lat1, lon1: Starting point coordinates
        lat2, lon2: Ending point coordinates
        
    Returns:
        Bearing in degrees (0-360)
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad))
    
    bearing_rad = math.atan2(y, x)
    bearing_deg = math.degrees(bearing_rad)
    
    # Normalize to 0-360
    return (bearing_deg + 360) % 360


def nm_to_km(nautical_miles: float) -> float:
    """Convert nautical miles to kilometers."""
    return nautical_miles * 1.852


def km_to_nm(kilometers: float) -> float:
    """Convert kilometers to nautical miles."""
    return kilometers / 1.852


def feet_to_meters(feet: float) -> float:
    """Convert feet to meters."""
    return feet * 0.3048


def meters_to_feet(meters: float) -> float:
    """Convert meters to feet."""
    return meters / 0.3048