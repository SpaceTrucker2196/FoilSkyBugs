"""
Database management for FoilSkyBugs.

Handles database connections, models, and operations.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

try:
    from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, text
    from sqlalchemy.orm import declarative_base, sessionmaker, Session
    from sqlalchemy.pool import StaticPool
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

from .adsb_decoder import Aircraft
from .config import DatabaseConfig

logger = logging.getLogger(__name__)

# Create base class for models
Base = declarative_base() if HAS_SQLALCHEMY else None


class AircraftPosition(Base):
    """Database model for aircraft positions."""
    __tablename__ = 'aircraft_positions'
    
    id = Column(Integer, primary_key=True)
    icao = Column(String(6), nullable=False, index=True)
    callsign = Column(String(8))
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Integer)
    speed = Column(Float)
    heading = Column(Float)
    vertical_rate = Column(Integer)
    squawk = Column(String(4))
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class FlightTrack(Base):
    """Database model for flight tracks."""
    __tablename__ = 'flight_tracks'
    
    id = Column(Integer, primary_key=True)
    icao = Column(String(6), nullable=False, index=True)
    callsign = Column(String(8), index=True)
    first_seen = Column(DateTime(timezone=True), nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=False)
    total_positions = Column(Integer, default=0)
    min_altitude = Column(Integer)
    max_altitude = Column(Integer)
    avg_speed = Column(Float)
    distance_traveled = Column(Float)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Statistics(Base):
    """Database model for statistics."""
    __tablename__ = 'statistics'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    total_aircraft = Column(Integer, default=0)
    total_positions = Column(Integer, default=0)
    unique_callsigns = Column(Integer, default=0)
    avg_altitude = Column(Float)
    max_altitude = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class DatabaseManager:
    """Database manager for FoilSkyBugs."""
    
    def __init__(self, config: DatabaseConfig):
        if not HAS_SQLALCHEMY:
            raise ImportError("SQLAlchemy is required but not installed. Install with: pip install sqlalchemy")
        
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _setup_database(self):
        """Setup database connection and create tables."""
        # Configure engine based on database URL
        if self.config.url.startswith('sqlite'):
            # SQLite specific configuration
            self.engine = create_engine(
                self.config.url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=False
            )
        else:
            # PostgreSQL or other databases
            self.engine = create_engine(
                self.config.url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=False
            )
        
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created/verified")
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def store_aircraft_position(self, aircraft: Aircraft) -> bool:
        """Store aircraft position in database."""
        try:
            with self.get_session() as session:
                position = AircraftPosition(
                    icao=aircraft.icao,
                    callsign=aircraft.callsign,
                    latitude=aircraft.latitude,
                    longitude=aircraft.longitude,
                    altitude=aircraft.altitude,
                    speed=aircraft.speed,
                    heading=aircraft.heading,
                    vertical_rate=aircraft.vertical_rate,
                    squawk=aircraft.squawk,
                    timestamp=aircraft.timestamp or datetime.now(timezone.utc)
                )
                session.add(position)
                return True
        except Exception as e:
            logger.error(f"Error storing aircraft position: {e}")
            return False
    
    def store_aircraft_positions(self, aircraft_list: List[Aircraft]) -> int:
        """Store multiple aircraft positions in database."""
        success_count = 0
        try:
            with self.get_session() as session:
                positions = []
                for aircraft in aircraft_list:
                    if aircraft.is_valid():
                        position = AircraftPosition(
                            icao=aircraft.icao,
                            callsign=aircraft.callsign,
                            latitude=aircraft.latitude,
                            longitude=aircraft.longitude,
                            altitude=aircraft.altitude,
                            speed=aircraft.speed,
                            heading=aircraft.heading,
                            vertical_rate=aircraft.vertical_rate,
                            squawk=aircraft.squawk,
                            timestamp=aircraft.timestamp or datetime.now(timezone.utc)
                        )
                        positions.append(position)
                
                session.add_all(positions)
                success_count = len(positions)
                
        except Exception as e:
            logger.error(f"Error storing aircraft positions: {e}")
        
        return success_count
    
    def get_aircraft_positions(self, icao: str = None, 
                             start_time: datetime = None,
                             end_time: datetime = None,
                             limit: int = 1000) -> List[Dict[str, Any]]:
        """Get aircraft positions from database."""
        try:
            with self.get_session() as session:
                query = session.query(AircraftPosition)
                
                if icao:
                    query = query.filter(AircraftPosition.icao == icao)
                
                if start_time:
                    query = query.filter(AircraftPosition.timestamp >= start_time)
                
                if end_time:
                    query = query.filter(AircraftPosition.timestamp <= end_time)
                
                query = query.order_by(AircraftPosition.timestamp.desc())
                query = query.limit(limit)
                
                positions = query.all()
                
                return [
                    {
                        'icao': pos.icao,
                        'callsign': pos.callsign,
                        'latitude': pos.latitude,
                        'longitude': pos.longitude,
                        'altitude': pos.altitude,
                        'speed': pos.speed,
                        'heading': pos.heading,
                        'vertical_rate': pos.vertical_rate,
                        'squawk': pos.squawk,
                        'timestamp': pos.timestamp.isoformat() if pos.timestamp else None
                    }
                    for pos in positions
                ]
        except Exception as e:
            logger.error(f"Error getting aircraft positions: {e}")
            return []
    
    def get_current_aircraft(self, max_age_minutes: int = 5) -> List[Dict[str, Any]]:
        """Get currently active aircraft."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
        
        try:
            with self.get_session() as session:
                # Get the latest position for each aircraft within the time window
                subquery = session.query(
                    AircraftPosition.icao,
                    session.query(AircraftPosition.timestamp)
                    .filter(AircraftPosition.icao == AircraftPosition.icao)
                    .filter(AircraftPosition.timestamp >= cutoff_time)
                    .order_by(AircraftPosition.timestamp.desc())
                    .limit(1)
                    .scalar_subquery()
                    .label('latest_timestamp')
                ).distinct().subquery()
                
                positions = session.query(AircraftPosition).join(
                    subquery,
                    (AircraftPosition.icao == subquery.c.icao) &
                    (AircraftPosition.timestamp == subquery.c.latest_timestamp)
                ).all()
                
                return [
                    {
                        'icao': pos.icao,
                        'callsign': pos.callsign,
                        'latitude': pos.latitude,
                        'longitude': pos.longitude,
                        'altitude': pos.altitude,
                        'speed': pos.speed,
                        'heading': pos.heading,
                        'vertical_rate': pos.vertical_rate,
                        'squawk': pos.squawk,
                        'timestamp': pos.timestamp.isoformat() if pos.timestamp else None
                    }
                    for pos in positions
                ]
        except Exception as e:
            logger.error(f"Error getting current aircraft: {e}")
            return []
    
    def update_statistics(self) -> bool:
        """Update daily statistics."""
        try:
            today = datetime.now(timezone.utc).date()
            start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_of_day = start_of_day + timedelta(days=1)
            
            with self.get_session() as session:
                # Calculate statistics for today
                positions_today = session.query(AircraftPosition).filter(
                    AircraftPosition.timestamp >= start_of_day,
                    AircraftPosition.timestamp < end_of_day
                ).all()
                
                if not positions_today:
                    return True
                
                unique_aircraft = set(pos.icao for pos in positions_today)
                unique_callsigns = set(pos.callsign for pos in positions_today if pos.callsign)
                altitudes = [pos.altitude for pos in positions_today if pos.altitude]
                
                stats = Statistics(
                    date=start_of_day,
                    total_aircraft=len(unique_aircraft),
                    total_positions=len(positions_today),
                    unique_callsigns=len(unique_callsigns),
                    avg_altitude=sum(altitudes) / len(altitudes) if altitudes else None,
                    max_altitude=max(altitudes) if altitudes else None
                )
                
                # Delete existing stats for today and insert new ones
                session.query(Statistics).filter(
                    Statistics.date >= start_of_day,
                    Statistics.date < end_of_day
                ).delete()
                
                session.add(stats)
                return True
                
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
            return False
    
    def cleanup_old_data(self) -> bool:
        """Clean up old data based on retention settings."""
        try:
            current_time = datetime.now(timezone.utc)
            positions_cutoff = current_time - timedelta(days=self.config.retention_positions)
            stats_cutoff = current_time - timedelta(days=self.config.retention_statistics)
            
            with self.get_session() as session:
                # Clean up old positions
                deleted_positions = session.query(AircraftPosition).filter(
                    AircraftPosition.timestamp < positions_cutoff
                ).delete()
                
                # Clean up old statistics
                deleted_stats = session.query(Statistics).filter(
                    Statistics.date < stats_cutoff
                ).delete()
                
                logger.info(f"Cleaned up {deleted_positions} old positions, {deleted_stats} old statistics")
                return True
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return False
    
    def get_statistics(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get statistics for the last N days."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            with self.get_session() as session:
                stats = session.query(Statistics).filter(
                    Statistics.date >= cutoff_date
                ).order_by(Statistics.date.desc()).all()
                
                return [
                    {
                        'date': stat.date.isoformat() if stat.date else None,
                        'total_aircraft': stat.total_aircraft,
                        'total_positions': stat.total_positions,
                        'unique_callsigns': stat.unique_callsigns,
                        'avg_altitude': stat.avg_altitude,
                        'max_altitude': stat.max_altitude
                    }
                    for stat in stats
                ]
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return []
    
    def health_check(self) -> bool:
        """Check database health."""
        try:
            with self.get_session() as session:
                # Simple query to test connection
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False