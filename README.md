# FoilSkyBugs

🛩️ **Advanced ADSB Data Logger & Analytics Platform**

FoilSkyBugs is a comprehensive ADSB (Automatic Dependent Surveillance-Broadcast) data logging and analysis system designed for aviation enthusiasts, researchers, and air traffic monitoring applications. Built with Python, it provides real-time aircraft tracking, data storage, and powerful analytics capabilities.

## 🚀 Project Overview

FoilSkyBugs captures, processes, and stores ADSB messages transmitted by aircraft, providing insights into flight patterns, aircraft movements, and aviation traffic analysis. The system is designed to be scalable, efficient, and easily deployable on various Linux distributions, with optimized support for Debian Trixie.

### Key Features

- **Real-time ADSB Data Processing**: Capture and decode ADSB messages from RTL-SDR dongles or network sources
- **Multi-source Data Ingestion**: Support for various ADSB data sources (RTL-SDR, network feeds, dump1090)
- **Efficient Data Storage**: Optimized database schema for high-frequency aircraft position updates
- **Geographic Filtering**: Configurable geographic boundaries for targeted monitoring
- **RESTful API**: HTTP API for data access and system control
- **Web Dashboard**: Real-time visualization of tracked aircraft
- **Data Export**: Export capabilities for analysis in external tools
- **Alert System**: Configurable alerts for specific aircraft or flight patterns

## 🏗️ Architecture Overview

FoilSkyBugs follows a modular, event-driven architecture designed for scalability and maintainability:

```
┌─────────────────────────────────────────────────────────────┐
│                    FoilSkyBugs Architecture                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌──────────────────┐    ┌──────────────┐
│   ADSB Sources  │    │   Data Ingestion │    │  Processing  │
│                 │    │                  │    │   Pipeline   │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌──────────┐ │
│ │ RTL-SDR     │ │───▶│ │ Message      │ │───▶│ │ Decoder  │ │
│ │ Hardware    │ │    │ │ Receiver     │ │    │ │ Engine   │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └──────────┘ │
│                 │    │                  │    │              │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌──────────┐ │
│ │ Network     │ │───▶│ │ Protocol     │ │───▶│ │ Position │ │
│ │ Feeds       │ │    │ │ Handler      │ │    │ │ Computer │ │
│ │ (dump1090)  │ │    │ └──────────────┘ │    │ └──────────┘ │
│ └─────────────┘ │    └──────────────────┘    └──────────────┘
└─────────────────┘                                     │
                                                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Services Layer                      │
├─────────────────┬──────────────────┬─────────────────────────┤
│   Database      │   API Server     │    Web Interface        │
│   Manager       │                  │                         │
│                 │ ┌──────────────┐ │ ┌─────────────────────┐ │
│ ┌─────────────┐ │ │ RESTful API  │ │ │ Real-time Dashboard │ │
│ │ PostgreSQL  │ │ │ Endpoints    │ │ │                     │ │
│ │ /SQLite     │ │ └──────────────┘ │ │ ┌─────────────────┐ │ │
│ └─────────────┘ │                  │ │ │ Aircraft Map    │ │ │
│                 │ ┌──────────────┐ │ │ │ (Leaflet.js)    │ │ │
│ ┌─────────────┐ │ │ WebSocket    │ │ │ └─────────────────┘ │ │
│ │ Time Series │ │ │ Real-time    │ │ │                     │ │
│ │ Optimization│ │ │ Updates      │ │ │ ┌─────────────────┐ │ │
│ └─────────────┘ │ └──────────────┘ │ │ │ Flight Lists    │ │ │
└─────────────────┴──────────────────┴─┼─┤ & Statistics    │ │ │
                                       │ └─────────────────┘ │ │
                                       └─────────────────────┘ │
                                         ┌─────────────────────┘
                                         ▼
                                ┌──────────────────┐
                                │   Alert Engine   │
                                │                  │
                                │ ┌──────────────┐ │
                                │ │ Rule Engine  │ │
                                │ └──────────────┘ │
                                │                  │
                                │ ┌──────────────┐ │
                                │ │ Notification │ │
                                │ │ Dispatcher   │ │
                                │ └──────────────┘ │
                                └──────────────────┘
```

### Component Descriptions

- **Data Ingestion Layer**: Handles multiple ADSB data sources with protocol-specific parsers
- **Processing Pipeline**: Decodes ADSB messages and computes aircraft positions and flight data
- **Database Manager**: Optimized storage with configurable backends (PostgreSQL/SQLite)
- **API Server**: RESTful and WebSocket APIs for real-time data access
- **Web Interface**: Browser-based dashboard for monitoring and analysis
- **Alert Engine**: Configurable monitoring and notification system

## 📊 Data Flow Diagram

The following diagram illustrates how ADSB data flows through the FoilSkyBugs system:

```
ADSB Data Flow Pipeline
─────────────────────────

Aircraft     RTL-SDR      Network
  📡     ──▶   📻    ──▶   🌐   ──┐
  │                              │
  │           Raw ADSB           │
  │          Messages            │
  │                              ▼
  │                      ┌─────────────────┐
  │                      │  Message Queue  │
  │                      │   (Optional)    │
  │                      └─────────────────┘
  │                              │
  │                              ▼
  │                      ┌─────────────────┐
  │                      │   ADSB Decoder  │
  │                      │                 │
  │                      │ • Mode S        │
  │                      │ • ADS-B         │
  │                      │ • Position Calc │
  │                      └─────────────────┘
  │                              │
  │              Decoded Aircraft Data
  │                              │
  │                              ▼
  │                      ┌─────────────────┐
  │                      │  Data Validator │
  │                      │                 │
  │                      │ • Range Check   │
  │                      │ • Duplicate Rem │
  │                      │ • Quality Score │
  │                      └─────────────────┘
  │                              │
  │                   Validated Position Data
  │                              │
  │                              ▼
  │                      ┌─────────────────┐
  │                      │   Geo Filter    │
  │                      │                 │
  │                      │ • Boundary Box  │
  │                      │ • Region Filter │
  │                      └─────────────────┘
  │                              │
  │                  ┌───────────┼───────────┐
  │                  │           │           │
  │                  ▼           ▼           ▼
  │          ┌──────────┐ ┌──────────┐ ┌──────────┐
  │          │ Database │ │ Real-time│ │  Alert   │
  │          │ Storage  │ │  API     │ │ Engine   │
  │          │          │ │          │ │          │
  │          │ •History │ │•WebSocket│ │•Rules    │
  │          │ •Archive │ │•REST API │ │•Triggers │
  │          └──────────┘ └──────────┘ └──────────┘
  │                  │           │           │
  │                  │           │           ▼
  │                  │           │    ┌──────────┐
  │                  │           │    │Notifications│
  │                  │           │    │          │
  │                  │           │    │ •Email   │
  │                  │           │    │ •Webhook │
  │                  │           │    │ •Slack   │
  │                  │           │    └──────────┘
  │                  │           │
  │                  │           ▼
  │                  │    ┌──────────────┐
  │                  │    │   Clients    │
  │                  │    │              │
  │                  │    │ •Web UI      │
  │                  │    │ •Mobile Apps │
  │                  │    │ •Third Party │
  │                  │    └──────────────┘
  │                  │
  │                  ▼
  │          ┌─────────────────┐
  │          │   Analytics     │
  │          │                 │
  │          │ • Flight Paths  │
  │          │ • Statistics    │
  │          │ • Reports       │
  │          │ • Data Export   │
  │          └─────────────────┘

Legend:
─────── Data Flow Direction
  📡    Aircraft Transmission
  📻    RTL-SDR Hardware
  🌐    Network Data Source
```

## 🔧 Dependencies

### System Requirements

- **Operating System**: Linux (Debian 12+ "Bookworm"/Trixie recommended)
- **Python**: 3.11 or higher
- **Memory**: Minimum 2GB RAM (4GB+ recommended for high-traffic areas)
- **Storage**: 10GB+ available space (depends on logging duration and area coverage)
- **Network**: Internet connection for initial setup and optional network ADSB feeds

### Hardware Requirements (Optional)

- **RTL-SDR Device**: RTL2832U-based USB dongle for direct ADSB reception
- **Antenna**: 1090MHz antenna optimized for ADSB reception
- **USB Port**: Available USB 2.0+ port for RTL-SDR device

### Python Dependencies

Core dependencies are automatically installed during setup:

```txt
# Core ADSB Processing
pyModeS>=2.13.0          # ADSB message decoding
pyrtlsdr>=0.2.92         # RTL-SDR hardware interface (optional)

# Database & Storage
psycopg2-binary>=2.9.5   # PostgreSQL adapter
SQLAlchemy>=2.0.0        # Database ORM
alembic>=1.13.0          # Database migrations

# Web Framework & API
Flask>=3.0.0             # Web framework
Flask-SocketIO>=5.3.0    # WebSocket support
Flask-CORS>=4.0.0        # Cross-origin resource sharing
Flask-RESTful>=0.3.10    # REST API utilities

# Data Processing & Analysis
numpy>=1.24.0            # Numerical computations
pandas>=2.1.0            # Data manipulation
geopy>=2.4.0             # Geographic calculations
shapely>=2.0.0           # Geometric operations

# Configuration & Utilities
pyyaml>=6.0.1            # Configuration file parsing
click>=8.1.0             # Command-line interface
python-dotenv>=1.0.0     # Environment variable management
schedule>=1.2.0          # Task scheduling
redis>=5.0.0             # Caching and message queuing (optional)

# Development & Testing
pytest>=7.4.0           # Testing framework
pytest-cov>=4.1.0       # Coverage reporting
black>=23.12.0          # Code formatting
flake8>=6.1.0           # Code linting
mypy>=1.8.0             # Type checking
```

### System Dependencies (Debian/Ubuntu)

```bash
# Essential build tools and libraries
sudo apt update
sudo apt install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-venv \
    pkg-config \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    git

# RTL-SDR support (optional, for hardware dongles)
sudo apt install -y \
    librtlsdr-dev \
    rtl-sdr

# Geographic and mathematical libraries
sudo apt install -y \
    libgeos-dev \
    libproj-dev \
    libgdal-dev

# Database servers (choose one)
# PostgreSQL (recommended for production)
sudo apt install -y postgresql postgresql-contrib

# OR SQLite (for development/testing)
sudo apt install -y sqlite3 libsqlite3-dev

# Web server (optional, for production deployment)
sudo apt install -y nginx

# Process management (optional, for production)
sudo apt install -y supervisor
```

## 🚀 Installation & Setup (Debian Trixie)

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/SpaceTrucker2196/FoilSkyBugs.git
   cd FoilSkyBugs
   ```

2. **Install System Dependencies**
   ```bash
   # Update package list
   sudo apt update

   # Install essential dependencies
   sudo apt install -y \
       python3.11 \
       python3.11-venv \
       python3.11-dev \
       python3-pip \
       build-essential \
       pkg-config \
       libffi-dev \
       libssl-dev \
       git

   # Install RTL-SDR support (if using hardware)
   sudo apt install -y librtlsdr-dev rtl-sdr

   # Install PostgreSQL (recommended)
   sudo apt install -y postgresql postgresql-contrib libpq-dev
   ```

3. **Create Python Virtual Environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip setuptools wheel
   ```

4. **Install FoilSkyBugs**
   ```bash
   # Install in development mode
   pip install -e .

   # OR install from requirements
   pip install -r requirements.txt
   ```

5. **Database Setup**
   ```bash
   # PostgreSQL setup
   sudo -u postgres createuser --interactive foilskybugs
   sudo -u postgres createdb foilskybugs_db -O foilskybugs

   # Initialize database schema
   foilskybugs db init
   foilskybugs db migrate
   ```

6. **Configuration**
   ```bash
   # Copy example configuration
   cp config/config.example.yaml config/config.yaml

   # Edit configuration file
   nano config/config.yaml
   ```

7. **Run the Application**
   ```bash
   # Start the ADSB data logger
   foilskybugs start --config config/config.yaml

   # In another terminal, start the web interface
   foilskybugs web --port 8080
   ```

### Advanced Installation Options

#### Production Deployment with systemd

1. **Create Service User**
   ```bash
   sudo useradd --system --shell /bin/false --home /opt/foilskybugs foilskybugs
   sudo mkdir -p /opt/foilskybugs
   sudo chown foilskybugs:foilskybugs /opt/foilskybugs
   ```

2. **Install to System Location**
   ```bash
   sudo -u foilskybugs git clone https://repo-url /opt/foilskybugs/app
   cd /opt/foilskybugs/app
   sudo -u foilskybugs python3 -m venv venv
   sudo -u foilskybugs venv/bin/pip install -e .
   ```

3. **Create systemd Service**
   ```bash
   sudo tee /etc/systemd/system/foilskybugs.service << EOF
   [Unit]
   Description=FoilSkyBugs ADSB Data Logger
   After=network.target postgresql.service
   Wants=postgresql.service

   [Service]
   Type=notify
   User=foilskybugs
   Group=foilskybugs
   WorkingDirectory=/opt/foilskybugs/app
   Environment=PATH=/opt/foilskybugs/app/venv/bin
   ExecStart=/opt/foilskybugs/app/venv/bin/foilskybugs start --config /opt/foilskybugs/config.yaml
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   EOF

   sudo systemctl daemon-reload
   sudo systemctl enable foilskybugs
   sudo systemctl start foilskybugs
   ```

#### Docker Deployment

```bash
# Build Docker image
docker build -t foilskybugs:latest .

# Run with Docker Compose
docker-compose up -d
```

## ⚙️ Configuration

FoilSkyBugs uses YAML configuration files. Copy `config/config.example.yaml` to `config/config.yaml` and customize:

### Example Configuration

```yaml
# FoilSkyBugs Configuration
app:
  name: "FoilSkyBugs"
  version: "1.0.0"
  environment: "production"  # development, testing, production

# ADSB Data Sources
data_sources:
  rtl_sdr:
    enabled: true
    device_index: 0
    frequency: 1090000000  # 1090 MHz
    sample_rate: 2000000   # 2 MHz
    gain: "auto"           # or specific value like 49.6

  network_feeds:
    - name: "dump1090"
      enabled: true
      host: "localhost"
      port: 30003
      format: "beast"      # beast, avr, sbs1

    - name: "external_feed"
      enabled: false
      url: "tcp://feed.example.com:30005"
      format: "beast"

# Geographic Filtering
geographic:
  # Bounding box for data collection (decimal degrees)
  bounds:
    north: 45.0
    south: 40.0
    east: -70.0
    west: -80.0

  # Center point for range calculations
  center:
    latitude: 42.5
    longitude: -75.0

  # Maximum range in nautical miles
  max_range: 250

# Database Configuration
database:
  # Primary database
  url: "postgresql://foilskybugs:password@localhost/foilskybugs_db"
  
  # Connection pool settings
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30
  pool_recycle: 3600

  # Data retention (days)
  retention:
    positions: 30      # Aircraft position reports
    tracks: 90         # Flight tracks
    statistics: 365    # Aggregated statistics

# Web Interface
web:
  host: "0.0.0.0"
  port: 8080
  debug: false
  secret_key: "your-secret-key-here"

  # Map configuration
  map:
    center_lat: 42.5
    center_lon: -75.0
    zoom: 8
    tile_server: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

# API Configuration
api:
  rate_limiting:
    enabled: true
    default_limit: "100/hour"
    
  authentication:
    enabled: false  # Set to true in production
    api_keys: []

# Alert System
alerts:
  enabled: true
  rules:
    - name: "emergency_squawk"
      condition: "squawk in ['7500', '7600', '7700']"
      action: "email"
      recipients: ["admin@example.com"]

    - name: "low_altitude"
      condition: "altitude < 1000 and speed > 200"
      action: "webhook"
      webhook_url: "https://example.com/webhook"

# Logging Configuration
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: "logs/foilskybugs.log"
  max_size: "10MB"
  backup_count: 5
  
  # Component-specific logging
  components:
    adsb_decoder: "DEBUG"
    database: "WARNING"
    web_api: "INFO"

# Performance Tuning
performance:
  # Processing batch sizes
  batch_sizes:
    message_processing: 100
    database_insert: 500
    
  # Caching
  cache:
    enabled: true
    backend: "redis"  # redis, memory
    redis_url: "redis://localhost:6379/0"
    default_timeout: 300

# Development Settings
development:
  auto_reload: true
  debug_toolbar: true
  profiling: false
```

## 🖥️ Usage Examples

### Command Line Interface

```bash
# Start the main data logger
foilskybugs start

# Start with specific configuration
foilskybugs start --config /path/to/config.yaml

# Start web interface only
foilskybugs web --port 8080

# Database operations
foilskybugs db init                    # Initialize database
foilskybugs db migrate                 # Run migrations
foilskybugs db backup --output backup.sql

# Data export
foilskybugs export --format csv --start "2024-01-01" --end "2024-01-02"
foilskybugs export --format geojson --bounds "40,-80,45,-70"

# Statistics and monitoring
foilskybugs stats --last-hour          # Show recent statistics
foilskybugs health                     # System health check
```

### API Usage Examples

```bash
# Get current aircraft in area
curl "http://localhost:8080/api/v1/aircraft/current"

# Get specific aircraft history
curl "http://localhost:8080/api/v1/aircraft/A1B2C3/history?hours=24"

# Get flights for specific date
curl "http://localhost:8080/api/v1/flights?date=2024-01-15"

# System statistics
curl "http://localhost:8080/api/v1/stats/summary"
```

### Python API Examples

```python
from foilskybugs import FoilSkyBugs, Config

# Initialize with configuration
config = Config.from_file('config.yaml')
tracker = FoilSkyBugs(config)

# Start data collection
tracker.start()

# Get current aircraft
aircraft = tracker.get_current_aircraft()
for ac in aircraft:
    print(f"Aircraft {ac.icao}: {ac.callsign} at {ac.latitude}, {ac.longitude}")

# Query historical data
from datetime import datetime, timedelta
end_time = datetime.now()
start_time = end_time - timedelta(hours=24)

flights = tracker.get_flights(start_time, end_time)
print(f"Found {len(flights)} flights in the last 24 hours")

# Export data
tracker.export_data(
    format='geojson',
    start_time=start_time,
    end_time=end_time,
    output_file='flights_24h.geojson'
)
```

## 🧪 Development Setup

### Setting up Development Environment

```bash
# Clone and enter directory
git clone https://github.com/SpaceTrucker2196/FoilSkyBugs.git
cd FoilSkyBugs

# Create development environment
python3 -m venv venv-dev
source venv-dev/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Code formatting and linting
black src/ tests/
flake8 src/ tests/
mypy src/
```

### Project Structure

```
FoilSkyBugs/
├── src/foilskybugs/           # Main application code
│   ├── __init__.py
│   ├── core/                  # Core functionality
│   │   ├── adsb_decoder.py
│   │   ├── database.py
│   │   └── config.py
│   ├── web/                   # Web interface
│   │   ├── app.py
│   │   ├── api/
│   │   └── templates/
│   ├── cli/                   # Command line interface
│   └── utils/                 # Utility functions
├── tests/                     # Test suite
├── config/                    # Configuration files
├── migrations/                # Database migrations
├── docs/                      # Documentation
├── docker/                    # Docker configurations
├── scripts/                   # Deployment scripts
├── requirements.txt           # Python dependencies
├── setup.py                   # Package setup
├── pytest.ini                # Test configuration
├── .pre-commit-config.yaml    # Pre-commit hooks
└── README.md                  # This file
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=foilskybugs --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Test specific components
pytest tests/test_adsb_decoder.py
pytest tests/test_database.py -v
```

### Contributing Guidelines

1. **Fork the Repository**: Create your own fork on GitHub
2. **Create Feature Branch**: `git checkout -b feature/your-feature-name`
3. **Write Tests**: Ensure your code has appropriate test coverage
4. **Follow Code Style**: Use `black` for formatting, `flake8` for linting
5. **Commit Messages**: Use clear, descriptive commit messages
6. **Submit Pull Request**: Submit PR with detailed description

### Code Style Guidelines

- **Python Style**: Follow PEP 8, enforced by `black` and `flake8`
- **Type Hints**: Use type hints for all public functions
- **Documentation**: Docstrings for all public classes and functions
- **Testing**: Minimum 80% test coverage for new code
- **Imports**: Use `isort` for import organization

## 📚 Additional Resources

### ADSB Resources

- [ADSB Wikipedia](https://en.wikipedia.org/wiki/Automatic_dependent_surveillance_%E2%80%93_broadcast)
- [Mode S and ADSB Decoding](https://mode-s.org/)
- [RTL-SDR Guide](https://www.rtl-sdr.com/rtl-sdr-tutorial-cheap-adsb-aircraft-radar/)

### Development Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [pyModeS Documentation](https://pymodes.readthedocs.io/)

### Hardware Recommendations

- **RTL-SDR**: FlightAware ProStick Plus, NooElec NESDR Smart v4
- **Antennas**: 1090MHz quarter-wave, FlightAware antenna
- **Filters**: SAW filter for 1090MHz to reduce interference

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and contribute to the project.

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/SpaceTrucker2196/FoilSkyBugs/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SpaceTrucker2196/FoilSkyBugs/discussions)
- **Email**: foilskybugs@example.com

## 🙏 Acknowledgments

- **pyModeS**: For excellent ADSB decoding capabilities
- **RTL-SDR Community**: For making affordable SDR possible  
- **OpenSky Network**: For inspiration and ADSB data insights
- **Aviation Community**: For continuous support and feedback

---

**✈️ Happy Aircraft Tracking!**

*Built with ❤️ for the aviation community*
