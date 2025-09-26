"""
Main CLI commands for FoilSkyBugs.
"""

import sys
import signal
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import click
    HAS_CLICK = True
except ImportError:
    HAS_CLICK = False

from ..core.config import Config
from ..core.foilskybugs import FoilSkyBugs


def ensure_click():
    """Ensure click is available."""
    if not HAS_CLICK:
        print("Error: click is required but not installed.")
        print("Install with: pip install click")
        sys.exit(1)


def signal_handler(signum, frame, app):
    """Handle shutdown signals."""
    print("\nShutting down FoilSkyBugs...")
    app.stop()
    sys.exit(0)


if HAS_CLICK:
    @click.group()
    @click.version_option(version="1.0.0", prog_name="FoilSkyBugs")
    def cli():
        """FoilSkyBugs - ADSB Data Logger & Analytics Platform"""
        pass
    
    
    @cli.command()
    @click.option('--config', '-c', default='config/config.yaml', 
                  help='Configuration file path')
    @click.option('--mock-data', is_flag=True, default=True,
                  help='Use mock ADSB data for testing')
    def start(config, mock_data):
        """Start the ADSB data collection and processing."""
        try:
            # Load configuration
            if Path(config).exists():
                app_config = Config.from_file(config)
            else:
                click.echo(f"Warning: Config file {config} not found, using defaults")
                app_config = Config()
            
            # Create and start FoilSkyBugs
            app = FoilSkyBugs(app_config)
            
            # Set up signal handlers
            signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, app))
            signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, app))
            
            # Start the application
            if app.start():
                click.echo("FoilSkyBugs started successfully")
                click.echo("Press Ctrl+C to stop")
                
                # Keep running until interrupted
                try:
                    while app.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
                finally:
                    app.stop()
                    click.echo("FoilSkyBugs stopped")
            else:
                click.echo("Failed to start FoilSkyBugs", err=True)
                sys.exit(1)
                
        except Exception as e:
            click.echo(f"Error starting FoilSkyBugs: {e}", err=True)
            sys.exit(1)
    
    
    @cli.command()
    @click.option('--config', '-c', default='config/config.yaml',
                  help='Configuration file path')
    @click.option('--port', '-p', default=8080, type=int,
                  help='Web server port')
    @click.option('--host', '-h', default='0.0.0.0',
                  help='Web server host')
    def web(config, port, host):
        """Start the web interface."""
        try:
            from ..web.app import create_app
            
            # Load configuration
            if Path(config).exists():
                app_config = Config.from_file(config)
            else:
                click.echo(f"Warning: Config file {config} not found, using defaults")
                app_config = Config()
            
            # Override web config with CLI options
            app_config.web.host = host
            app_config.web.port = port
            
            # Create Flask app
            flask_app = create_app(app_config)
            
            click.echo(f"Starting web interface on http://{host}:{port}")
            flask_app.run(host=host, port=port, debug=app_config.web.debug)
            
        except ImportError:
            click.echo("Error: Flask is required for web interface", err=True)
            click.echo("Install with: pip install flask flask-cors", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error starting web interface: {e}", err=True)
            sys.exit(1)
    
    
    @cli.group()
    def db():
        """Database management commands."""
        pass
    
    
    @db.command()
    @click.option('--config', '-c', default='config/config.yaml',
                  help='Configuration file path')
    def init(config):
        """Initialize the database."""
        try:
            # Load configuration
            if Path(config).exists():
                app_config = Config.from_file(config)
            else:
                click.echo(f"Warning: Config file {config} not found, using defaults")
                app_config = Config()
            
            from ..core.database import DatabaseManager
            
            # Initialize database
            db_manager = DatabaseManager(app_config.database)
            
            if db_manager.health_check():
                click.echo("Database initialized successfully")
            else:
                click.echo("Database initialization failed", err=True)
                sys.exit(1)
                
        except Exception as e:
            click.echo(f"Error initializing database: {e}", err=True)
            sys.exit(1)
    
    
    @db.command()
    @click.option('--config', '-c', default='config/config.yaml',
                  help='Configuration file path')
    def migrate(config):
        """Run database migrations."""
        click.echo("Database migrations completed (placeholder)")
    
    
    @cli.command()
    @click.option('--config', '-c', default='config/config.yaml',
                  help='Configuration file path')
    @click.option('--format', '-f', default='json', 
                  type=click.Choice(['json', 'csv', 'geojson']),
                  help='Export format')
    @click.option('--start', help='Start date (YYYY-MM-DD)')
    @click.option('--end', help='End date (YYYY-MM-DD)')
    @click.option('--bounds', help='Geographic bounds (south,west,north,east)')
    @click.option('--output', '-o', help='Output file path')
    def export(config, format, start, end, bounds, output):
        """Export ADSB data."""
        try:
            # Load configuration
            if Path(config).exists():
                app_config = Config.from_file(config)
            else:
                click.echo(f"Warning: Config file {config} not found, using defaults")
                app_config = Config()
            
            # Create FoilSkyBugs instance
            app = FoilSkyBugs(app_config)
            
            # Parse dates
            start_time = None
            end_time = None
            
            if start:
                start_time = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
            
            if end:
                end_time = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
            elif start_time:
                end_time = start_time + timedelta(days=1)
            
            # Export data
            success = app.export_data(
                format=format,
                start_time=start_time,
                end_time=end_time,
                output_file=output,
                bounds=bounds
            )
            
            if success:
                click.echo(f"Data exported successfully in {format} format")
            else:
                click.echo("Export failed", err=True)
                sys.exit(1)
                
        except Exception as e:
            click.echo(f"Error exporting data: {e}", err=True)
            sys.exit(1)
    
    
    @cli.command()
    @click.option('--config', '-c', default='config/config.yaml',
                  help='Configuration file path')
    @click.option('--last-hour', is_flag=True,
                  help='Show statistics for the last hour')
    def stats(config, last_hour):
        """Show system statistics."""
        try:
            # Load configuration
            if Path(config).exists():
                app_config = Config.from_file(config)
            else:
                click.echo(f"Warning: Config file {config} not found, using defaults")
                app_config = Config()
            
            # Create FoilSkyBugs instance
            app = FoilSkyBugs(app_config)
            
            if last_hour:
                # Show current aircraft count
                aircraft = app.get_current_aircraft()
                click.echo(f"Current aircraft: {len(aircraft)}")
                
                for ac in aircraft[:10]:  # Show first 10
                    click.echo(f"  {ac['icao']}: {ac.get('callsign', 'N/A')} "
                             f"at {ac.get('altitude', 'N/A')}ft")
            else:
                # Show historical statistics
                stats = app.get_statistics(days=7)
                
                if stats:
                    click.echo("Statistics (last 7 days):")
                    click.echo("Date\t\tAircraft\tPositions\tCallsigns")
                    click.echo("-" * 60)
                    
                    for stat in stats:
                        date = stat['date'][:10] if stat['date'] else 'N/A'
                        click.echo(f"{date}\t{stat['total_aircraft']}\t\t"
                                 f"{stat['total_positions']}\t\t{stat['unique_callsigns']}")
                else:
                    click.echo("No statistics available")
                    
        except Exception as e:
            click.echo(f"Error getting statistics: {e}", err=True)
            sys.exit(1)
    
    
    @cli.command()
    @click.option('--config', '-c', default='config/config.yaml',
                  help='Configuration file path')
    def health(config):
        """System health check."""
        try:
            # Load configuration
            if Path(config).exists():
                app_config = Config.from_file(config)
            else:
                click.echo(f"Warning: Config file {config} not found, using defaults")
                app_config = Config()
            
            # Create FoilSkyBugs instance
            app = FoilSkyBugs(app_config)
            
            # Perform health check
            health = app.health_check()
            
            click.echo(f"Overall Status: {health['status'].upper()}")
            click.echo(f"Timestamp: {health['timestamp']}")
            click.echo("\nComponent Status:")
            
            for component, status in health['components'].items():
                click.echo(f"  {component}: {status['status'].upper()}")
                if 'message' in status:
                    click.echo(f"    {status['message']}")
                if 'current_aircraft' in status:
                    click.echo(f"    Current aircraft: {status['current_aircraft']}")
            
            if health['status'] != 'healthy':
                sys.exit(1)
                
        except Exception as e:
            click.echo(f"Error performing health check: {e}", err=True)
            sys.exit(1)

else:
    # Fallback CLI without click
    def cli():
        ensure_click()


if __name__ == '__main__':
    cli()