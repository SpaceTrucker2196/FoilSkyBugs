"""
FoilSkyBugs - Advanced ADSB Data Logger & Analytics Platform

A comprehensive ADSB data logging and analysis system for aviation enthusiasts,
researchers, and air traffic monitoring applications.
"""

__version__ = "1.0.0"
__author__ = "SpaceTrucker2196"
__email__ = "foilskybugs@example.com"

from .core.config import Config
from .core.foilskybugs import FoilSkyBugs

__all__ = ["Config", "FoilSkyBugs", "__version__"]