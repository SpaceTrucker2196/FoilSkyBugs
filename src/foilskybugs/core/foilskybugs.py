"""
Main FoilSkyBugs class - ADSB Data Logger & Analytics Platform.

Coordinates all components and provides the main API interface.
"""

import logging
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import json

from .config import Config
from .adsb_decoder import ADSBDecoder, Aircraft
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class FoilSkyBugs:
    """Main FoilSkyBugs application class."""
    
    def __init__(self, config: Config):
        self.config = config
        self.running = False
        self.data_thread = None
        
        # Initialize components
        self.decoder = ADSBDecoder(use_mock_data=True)  # Default to mock data
        self.database = DatabaseManager(config.database)
        
        # Setup logging
        self._setup_logging()
        
        logger.info(f"FoilSkyBugs initialized - {config.app_name} v{config.app_version}")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.log_file),
                logging.StreamHandler()
            ]
        )
    
    def start(self):
        """Start the ADSB data collection and processing."""
        if self.running:
            logger.warning("FoilSkyBugs is already running")
            return False
        
        logger.info("Starting FoilSkyBugs data collection")
        self.running = True
        
        # Start data collection thread
        self.data_thread = threading.Thread(target=self._data_collection_loop, daemon=True)
        self.data_thread.start()
        
        return True
    
    def stop(self):
        """Stop the ADSB data collection and processing."""
        if not self.running:
            logger.warning("FoilSkyBugs is not running")
            return False
        
        logger.info("Stopping FoilSkyBugs data collection")
        self.running = False
        
        if self.data_thread and self.data_thread.is_alive():
            self.data_thread.join(timeout=5)
        
        return True
    
    def _data_collection_loop(self):
        """Main data collection and processing loop."""
        logger.info("Data collection loop started")
        
        last_cleanup = time.time()
        last_stats_update = time.time()
        
        while self.running:
            try:
                # Get current aircraft data
                aircraft_list = self.decoder.get_current_aircraft()
                
                if aircraft_list:
                    # Store in database
                    stored_count = self.database.store_aircraft_positions(aircraft_list)
                    if stored_count > 0:
                        logger.debug(f"Stored {stored_count} aircraft positions")
                
                # Periodic maintenance tasks
                current_time = time.time()
                
                # Cleanup old aircraft from decoder cache (every 5 minutes)
                if current_time - last_cleanup > 300:
                    self.decoder.cleanup_old_aircraft()
                    last_cleanup = current_time
                
                # Update statistics (every hour)
                if current_time - last_stats_update > 3600:
                    self.database.update_statistics()
                    last_stats_update = current_time
                
            except Exception as e:
                logger.error(f"Error in data collection loop: {e}")
            
            # Sleep for a short interval
            time.sleep(5)
        
        logger.info("Data collection loop stopped")
    
    def get_current_aircraft(self) -> List[Dict[str, Any]]:
        """Get list of currently tracked aircraft."""
        # First try to get from decoder (most recent data)
        aircraft_list = self.decoder.get_current_aircraft()
        
        if aircraft_list:
            return [aircraft.to_dict() for aircraft in aircraft_list]
        
        # Fall back to database
        return self.database.get_current_aircraft()
    
    def get_aircraft_by_icao(self, icao: str) -> Optional[Dict[str, Any]]:
        """Get specific aircraft by ICAO code."""
        # Try decoder first
        aircraft = self.decoder.get_aircraft_by_icao(icao)
        if aircraft:
            return aircraft.to_dict()
        
        # Fall back to database
        positions = self.database.get_aircraft_positions(icao=icao, limit=1)
        return positions[0] if positions else None
    
    def get_aircraft_history(self, icao: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical positions for an aircraft."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        return self.database.get_aircraft_positions(
            icao=icao,
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
    
    def get_flights(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get flights for a time period."""
        return self.database.get_aircraft_positions(
            start_time=start_time,
            end_time=end_time,
            limit=5000
        )
    
    def get_statistics(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get statistics for the last N days."""
        return self.database.get_statistics(days=days)
    
    def export_data(self, format: str = 'json', start_time: datetime = None,
                   end_time: datetime = None, output_file: str = None,
                   bounds: str = None) -> bool:
        """Export data in various formats."""
        try:
            # Get data from database
            positions = self.database.get_aircraft_positions(
                start_time=start_time,
                end_time=end_time,
                limit=10000
            )
            
            if not positions:
                logger.warning("No data to export")
                return False
            
            # Apply geographic bounds if specified
            if bounds:
                try:
                    bounds_parts = bounds.split(',')
                    if len(bounds_parts) == 4:
                        south, west, north, east = map(float, bounds_parts)
                        positions = [
                            pos for pos in positions
                            if (pos['latitude'] and pos['longitude'] and
                                south <= pos['latitude'] <= north and
                                west <= pos['longitude'] <= east)
                        ]
                except ValueError:
                    logger.error(f"Invalid bounds format: {bounds}")
                    return False
            
            # Export in specified format
            if format.lower() == 'json':
                return self._export_json(positions, output_file)
            elif format.lower() == 'csv':
                return self._export_csv(positions, output_file)
            elif format.lower() == 'geojson':
                return self._export_geojson(positions, output_file)
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False
    
    def _export_json(self, positions: List[Dict[str, Any]], output_file: str = None) -> bool:
        """Export data as JSON."""
        try:
            filename = output_file or f"foilskybugs_export_{int(time.time())}.json"
            
            with open(filename, 'w') as f:
                json.dump({
                    'export_time': datetime.now(timezone.utc).isoformat(),
                    'total_positions': len(positions),
                    'positions': positions
                }, f, indent=2)
            
            logger.info(f"Exported {len(positions)} positions to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            return False
    
    def _export_csv(self, positions: List[Dict[str, Any]], output_file: str = None) -> bool:
        """Export data as CSV."""
        try:
            import csv
            
            filename = output_file or f"foilskybugs_export_{int(time.time())}.csv"
            
            if not positions:
                return False
            
            with open(filename, 'w', newline='') as f:
                fieldnames = positions[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                for position in positions:
                    writer.writerow(position)
            
            logger.info(f"Exported {len(positions)} positions to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return False
    
    def _export_geojson(self, positions: List[Dict[str, Any]], output_file: str = None) -> bool:
        """Export data as GeoJSON."""
        try:
            filename = output_file or f"foilskybugs_export_{int(time.time())}.geojson"
            
            features = []
            for position in positions:
                if position['latitude'] and position['longitude']:
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [position['longitude'], position['latitude']]
                        },
                        "properties": {
                            "icao": position['icao'],
                            "callsign": position['callsign'],
                            "altitude": position['altitude'],
                            "speed": position['speed'],
                            "heading": position['heading'],
                            "squawk": position['squawk'],
                            "timestamp": position['timestamp']
                        }
                    }
                    features.append(feature)
            
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            with open(filename, 'w') as f:
                json.dump(geojson, f, indent=2)
            
            logger.info(f"Exported {len(features)} positions to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting GeoJSON: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform system health check."""
        health = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'components': {}
        }
        
        # Check database
        try:
            db_healthy = self.database.health_check()
            health['components']['database'] = {
                'status': 'healthy' if db_healthy else 'unhealthy',
                'message': 'Connection OK' if db_healthy else 'Connection failed'
            }
        except Exception as e:
            health['components']['database'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        # Check data collection
        health['components']['data_collection'] = {
            'status': 'running' if self.running else 'stopped',
            'thread_alive': self.data_thread.is_alive() if self.data_thread else False
        }
        
        # Check decoder
        try:
            aircraft_count = len(self.decoder.get_current_aircraft())
            health['components']['decoder'] = {
                'status': 'healthy',
                'current_aircraft': aircraft_count
            }
        except Exception as e:
            health['components']['decoder'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        # Overall status
        unhealthy_components = [
            comp for comp, status in health['components'].items()
            if status.get('status') in ['unhealthy', 'stopped']
        ]
        
        if unhealthy_components:
            health['status'] = 'degraded'
            health['issues'] = unhealthy_components
        
        return health