"""
Flask web application for FoilSkyBugs.
"""

import logging
from datetime import datetime, timezone, timedelta

try:
    from flask import Flask, jsonify, request, render_template_string
    from flask_cors import CORS
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

from ..core.config import Config
from ..core.foilskybugs import FoilSkyBugs

logger = logging.getLogger(__name__)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>FoilSkyBugs - ADSB Tracker</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 1rem;
            text-align: center;
        }
        .container {
            display: flex;
            height: calc(100vh - 80px);
        }
        .sidebar {
            width: 300px;
            background-color: white;
            border-right: 1px solid #ddd;
            overflow-y: auto;
            padding: 1rem;
        }
        .map-container {
            flex: 1;
            position: relative;
        }
        #map {
            height: 100%;
            width: 100%;
        }
        .aircraft-item {
            padding: 0.5rem;
            border-bottom: 1px solid #eee;
            cursor: pointer;
        }
        .aircraft-item:hover {
            background-color: #f8f9fa;
        }
        .aircraft-icao {
            font-weight: bold;
            color: #2c3e50;
        }
        .aircraft-callsign {
            color: #3498db;
        }
        .aircraft-details {
            font-size: 0.8em;
            color: #666;
        }
        .stats {
            background-color: #ecf0f1;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }
        .refresh-btn {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 1rem;
        }
        .refresh-btn:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛩️ FoilSkyBugs - ADSB Tracker</h1>
        <p>Real-time Aircraft Tracking</p>
    </div>
    
    <div class="container">
        <div class="sidebar">
            <button class="refresh-btn" onclick="refreshData()">Refresh Data</button>
            
            <div class="stats">
                <h3>Statistics</h3>
                <div id="stats">Loading...</div>
            </div>
            
            <div>
                <h3>Current Aircraft</h3>
                <div id="aircraft-list">Loading...</div>
            </div>
        </div>
        
        <div class="map-container">
            <div id="map"></div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Initialize map
        const map = L.map('map').setView([42.5, -75.0], 8);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        
        let aircraftMarkers = {};
        
        // Aircraft icon
        const aircraftIcon = L.divIcon({
            className: 'aircraft-marker',
            html: '✈️',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });
        
        function refreshData() {
            fetch('/api/v1/aircraft/current')
                .then(response => response.json())
                .then(data => {
                    updateAircraftList(data);
                    updateMap(data);
                })
                .catch(error => {
                    console.error('Error fetching aircraft data:', error);
                });
            
            fetch('/api/v1/stats/summary')
                .then(response => response.json())
                .then(data => {
                    updateStats(data);
                })
                .catch(error => {
                    console.error('Error fetching stats:', error);
                });
        }
        
        function updateAircraftList(aircraft) {
            const listElement = document.getElementById('aircraft-list');
            if (!aircraft || aircraft.length === 0) {
                listElement.innerHTML = '<p>No aircraft currently tracked</p>';
                return;
            }
            
            const html = aircraft.map(ac => `
                <div class="aircraft-item" onclick="focusAircraft('${ac.icao}')">
                    <div class="aircraft-icao">${ac.icao}</div>
                    <div class="aircraft-callsign">${ac.callsign || 'N/A'}</div>
                    <div class="aircraft-details">
                        Alt: ${ac.altitude ? ac.altitude + 'ft' : 'N/A'}<br>
                        Speed: ${ac.speed ? ac.speed + 'kts' : 'N/A'}<br>
                        Heading: ${ac.heading !== null ? ac.heading + '°' : 'N/A'}
                    </div>
                </div>
            `).join('');
            
            listElement.innerHTML = html;
        }
        
        function updateMap(aircraft) {
            // Clear existing markers
            Object.values(aircraftMarkers).forEach(marker => {
                map.removeLayer(marker);
            });
            aircraftMarkers = {};
            
            // Add new markers
            aircraft.forEach(ac => {
                if (ac.latitude && ac.longitude) {
                    const marker = L.marker([ac.latitude, ac.longitude], {icon: aircraftIcon})
                        .addTo(map);
                    
                    const popupContent = `
                        <strong>${ac.icao}</strong><br>
                        Callsign: ${ac.callsign || 'N/A'}<br>
                        Altitude: ${ac.altitude ? ac.altitude + 'ft' : 'N/A'}<br>
                        Speed: ${ac.speed ? ac.speed + 'kts' : 'N/A'}<br>
                        Heading: ${ac.heading !== null ? ac.heading + '°' : 'N/A'}<br>
                        Squawk: ${ac.squawk || 'N/A'}
                    `;
                    
                    marker.bindPopup(popupContent);
                    aircraftMarkers[ac.icao] = marker;
                }
            });
        }
        
        function updateStats(stats) {
            const statsElement = document.getElementById('stats');
            const currentAircraft = Object.keys(aircraftMarkers).length;
            
            statsElement.innerHTML = `
                <strong>Current Aircraft:</strong> ${currentAircraft}<br>
                <strong>System Status:</strong> ${stats.status || 'Unknown'}<br>
                <strong>Last Update:</strong> ${new Date().toLocaleTimeString()}
            `;
        }
        
        function focusAircraft(icao) {
            const marker = aircraftMarkers[icao];
            if (marker) {
                map.setView(marker.getLatLng(), 10);
                marker.openPopup();
            }
        }
        
        // Auto-refresh every 10 seconds
        setInterval(refreshData, 10000);
        
        // Initial load
        refreshData();
    </script>
</body>
</html>
"""


def create_app(config: Config) -> Flask:
    """Create and configure Flask application."""
    if not HAS_FLASK:
        raise ImportError("Flask is required but not installed. Install with: pip install flask flask-cors")
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.web.secret_key
    
    # Enable CORS for API endpoints
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Create FoilSkyBugs instance
    foilskybugs = FoilSkyBugs(config)
    
    @app.route('/')
    def index():
        """Main dashboard page."""
        return render_template_string(HTML_TEMPLATE)
    
    @app.route('/api/v1/aircraft/current')
    def get_current_aircraft():
        """Get currently tracked aircraft."""
        try:
            aircraft = foilskybugs.get_current_aircraft()
            return jsonify(aircraft)
        except Exception as e:
            logger.error(f"Error getting current aircraft: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/aircraft/<icao>')
    def get_aircraft(icao):
        """Get specific aircraft by ICAO."""
        try:
            aircraft = foilskybugs.get_aircraft_by_icao(icao.upper())
            if aircraft:
                return jsonify(aircraft)
            else:
                return jsonify({'error': 'Aircraft not found'}), 404
        except Exception as e:
            logger.error(f"Error getting aircraft {icao}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/aircraft/<icao>/history')
    def get_aircraft_history(icao):
        """Get aircraft position history."""
        try:
            hours = request.args.get('hours', 24, type=int)
            history = foilskybugs.get_aircraft_history(icao.upper(), hours=hours)
            return jsonify(history)
        except Exception as e:
            logger.error(f"Error getting aircraft history for {icao}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/flights')
    def get_flights():
        """Get flights for a date range."""
        try:
            date = request.args.get('date')
            if date:
                start_time = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
                end_time = start_time + timedelta(days=1)
            else:
                # Default to last 24 hours
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=24)
            
            flights = foilskybugs.get_flights(start_time, end_time)
            return jsonify(flights)
        except Exception as e:
            logger.error(f"Error getting flights: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/stats/summary')
    def get_stats_summary():
        """Get system statistics summary."""
        try:
            health = foilskybugs.health_check()
            stats = foilskybugs.get_statistics(days=1)
            
            current_aircraft = foilskybugs.get_current_aircraft()
            
            summary = {
                'status': health['status'],
                'current_aircraft_count': len(current_aircraft),
                'timestamp': health['timestamp']
            }
            
            if stats:
                latest_stats = stats[0]
                summary.update({
                    'daily_aircraft': latest_stats.get('total_aircraft', 0),
                    'daily_positions': latest_stats.get('total_positions', 0),
                    'unique_callsigns': latest_stats.get('unique_callsigns', 0)
                })
            
            return jsonify(summary)
        except Exception as e:
            logger.error(f"Error getting stats summary: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/health')
    def health_check():
        """System health check."""
        try:
            health = foilskybugs.health_check()
            status_code = 200 if health['status'] == 'healthy' else 503
            return jsonify(health), status_code
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({'error': 'Internal server error'}), 500
    
    return app