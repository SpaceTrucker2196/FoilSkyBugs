#!/usr/bin/env python3
"""
Demo script for FoilSkyBugs ADSB platform.

This script demonstrates the basic functionality of FoilSkyBugs.
"""

import sys
import time
import json
from pathlib import Path

# Add src to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from foilskybugs.core.config import Config
from foilskybugs.core.foilskybugs import FoilSkyBugs


def main():
    """Run the demo."""
    print("🛩️  FoilSkyBugs ADSB Platform Demo")
    print("=" * 50)
    
    # Create default configuration
    config = Config()
    print(f"Using database: {config.database.url}")
    
    # Initialize FoilSkyBugs
    print("\n1. Initializing FoilSkyBugs...")
    app = FoilSkyBugs(config)
    print("✓ FoilSkyBugs initialized successfully")
    
    # Health check
    print("\n2. Performing health check...")
    health = app.health_check()
    print(f"✓ System status: {health['status'].upper()}")
    for component, status in health['components'].items():
        print(f"  - {component}: {status['status'].upper()}")
    
    # Start data collection
    print("\n3. Starting data collection...")
    if app.start():
        print("✓ Data collection started")
        
        # Collect data for a few seconds
        print("\n4. Collecting ADSB data (mock data)...")
        for i in range(5):
            aircraft = app.get_current_aircraft()
            print(f"  - Cycle {i+1}: {len(aircraft)} aircraft tracked")
            time.sleep(2)
        
        # Show some aircraft details
        print("\n5. Current aircraft details:")
        aircraft_list = app.get_current_aircraft()
        
        for i, aircraft in enumerate(aircraft_list[:5]):  # Show first 5
            print(f"  Aircraft {i+1}:")
            print(f"    ICAO: {aircraft['icao']}")
            print(f"    Callsign: {aircraft.get('callsign', 'N/A')}")
            print(f"    Position: {aircraft.get('latitude', 'N/A')}, {aircraft.get('longitude', 'N/A')}")
            print(f"    Altitude: {aircraft.get('altitude', 'N/A')} ft")
            print(f"    Speed: {aircraft.get('speed', 'N/A')} kts")
            print(f"    Heading: {aircraft.get('heading', 'N/A')}°")
            print()
        
        # Test aircraft tracking
        if aircraft_list:
            test_icao = aircraft_list[0]['icao']
            print(f"6. Testing aircraft tracking for {test_icao}...")
            
            specific_aircraft = app.get_aircraft_by_icao(test_icao)
            if specific_aircraft:
                print(f"✓ Found aircraft {test_icao}")
            
            # Get history (will be limited since we just started)
            history = app.get_aircraft_history(test_icao, hours=1)
            print(f"✓ Aircraft has {len(history)} position reports")
        
        # Test data export
        print("\n7. Testing data export...")
        export_file = "/tmp/foilskybugs_demo_export.json"
        success = app.export_data(format='json', output_file=export_file)
        if success:
            print(f"✓ Data exported to {export_file}")
            # Show export size
            import os
            if os.path.exists(export_file):
                size = os.path.getsize(export_file)
                print(f"  Export file size: {size} bytes")
        else:
            print("⚠ No data to export (expected for short demo)")
        
        # Final health check
        print("\n8. Final health check...")
        health = app.health_check()
        print(f"✓ System status: {health['status'].upper()}")
        
        # Stop data collection
        print("\n9. Stopping data collection...")
        app.stop()
        print("✓ Data collection stopped")
        
    else:
        print("✗ Failed to start data collection")
        return 1
    
    print("\n🎉 Demo completed successfully!")
    print("\nNext steps:")
    print("- Configure real ADSB data sources in config/config.yaml")
    print("- Start the web interface: foilskybugs web")
    print("- View real-time aircraft tracking in your browser")
    print("- Set up database for production use")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Demo failed: {e}")
        sys.exit(1)