# FoilSkyBugs Installation Guide

This guide covers installing FoilSkyBugs as a system-wide service on Debian/Ubuntu systems.

## 🚀 Quick Installation

### Prerequisites

- Debian 11+ or Ubuntu 20.04+ (Debian Trixie recommended)
- Root/sudo access
- Internet connection for package downloads

### System Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SpaceTrucker2196/FoilSkyBugs.git
   cd FoilSkyBugs
   ```

2. **Run the installation script:**
   ```bash
   sudo ./install.sh
   ```

   **Optional installations:**
   ```bash
   # With PostgreSQL support
   sudo ./install.sh --with-postgresql
   
   # With RTL-SDR hardware support
   sudo ./install.sh --with-rtlsdr
   
   # With both
   sudo ./install.sh --with-postgresql --with-rtlsdr
   ```

3. **Start the services:**
   ```bash
   sudo ./start.sh
   ```

## 🔧 Manual Installation

If you prefer to install manually or for development:

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

2. **Initialize database:**
   ```bash
   foilskybugs db init
   ```

3. **Start application:**
   ```bash
   foilskybugs start --config config/config.yaml
   ```

4. **Start web interface (separate terminal):**
   ```bash
   foilskybugs web --port 8080
   ```

## 📋 Service Management

After system installation, use the start script for service management:

### Start Services
```bash
sudo ./start.sh                    # Start all services
sudo ./start.sh --web-only         # Start only web interface
sudo ./start.sh --data-only        # Start only data collection
```

### Check Status
```bash
sudo ./start.sh --status           # Show service status
foilskybugs health                 # Application health check
```

### Manage Services
```bash
sudo ./start.sh --stop             # Stop all services
sudo ./start.sh --restart          # Restart all services
sudo ./start.sh --logs             # View service logs
```

### Direct systemctl Commands
```bash
# Data collection service
sudo systemctl start foilskybugs
sudo systemctl stop foilskybugs
sudo systemctl status foilskybugs

# Web interface service
sudo systemctl start foilskybugs-web
sudo systemctl stop foilskybugs-web
sudo systemctl status foilskybugs-web
```

## 🌐 Accessing the Web Interface

After starting the services:

- **URL:** http://localhost:8080
- **Default Config:** Real-time aircraft tracking with mock data
- **API Endpoints:** http://localhost:8080/api/v1/

### API Examples
```bash
# Get current aircraft
curl "http://localhost:8080/api/v1/aircraft/current"

# System health
curl "http://localhost:8080/api/v1/health"

# Statistics
curl "http://localhost:8080/api/v1/stats/summary"
```

## ⚙️ Configuration

### System Configuration
- **Main Config:** `/etc/foilskybugs/config.yaml`
- **Service Files:** `/etc/systemd/system/foilskybugs*.service`
- **Data Directory:** `/var/lib/foilskybugs/`
- **Logs:** `/var/log/foilskybugs/`

### Development Configuration
- **Config:** `config/config.yaml`
- **Database:** `foilskybugs.db` (SQLite)
- **Logs:** `foilskybugs.log`

### Example Configuration Updates
```bash
# Edit system configuration
sudo nano /etc/foilskybugs/config.yaml

# Edit development configuration
nano config/config.yaml

# After changes, restart services
sudo ./start.sh --restart
```

## 🗄️ Database Setup

### SQLite (Default)
No additional setup required. Database is automatically created.

### PostgreSQL (Recommended for Production)
```bash
# Install with PostgreSQL support
sudo ./install.sh --with-postgresql

# Or configure manually
sudo -u postgres createuser --interactive foilskybugs
sudo -u postgres createdb foilskybugs_db -O foilskybugs

# Update config.yaml
database:
  url: "postgresql://foilskybugs:password@localhost/foilskybugs_db"
```

## 📡 ADSB Data Sources

### Mock Data (Default)
FoilSkyBugs includes comprehensive mock data for testing and demonstration.

### dump1090 Integration
```yaml
# Edit config.yaml
data_sources:
  network_feeds:
    - name: "dump1090"
      enabled: true
      host: "localhost"
      port: 30003
      format: "beast"
```

### RTL-SDR Hardware
```bash
# Install with RTL-SDR support
sudo ./install.sh --with-rtlsdr

# Configure in config.yaml
data_sources:
  rtl_sdr:
    enabled: true
    device_index: 0
    frequency: 1090000000
    gain: "auto"
```

## 🔍 Troubleshooting

### Command Not Found
```bash
# Check if installed
which foilskybugs

# Reinstall if needed
sudo ./install.sh

# For development installation
pip install -e .
```

### Service Issues
```bash
# Check service status
sudo ./start.sh --status

# View logs
sudo ./start.sh --logs
journalctl -u foilskybugs -f

# Health check
foilskybugs health
```

### Permission Issues
```bash
# Check file permissions
ls -la /etc/foilskybugs/
ls -la /var/lib/foilskybugs/

# Fix permissions if needed
sudo chown -R foilskybugs:foilskybugs /var/lib/foilskybugs/
sudo chown -R foilskybugs:foilskybugs /var/log/foilskybugs/
```

### Database Issues
```bash
# Reinitialize database
foilskybugs db init

# For system installation
sudo -u foilskybugs foilskybugs db init --config /etc/foilskybugs/config.yaml
```

## 📊 Testing Installation

### Run Test Suite
```bash
# Install test dependencies
pip install pytest pytest-mock

# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

### Verify Installation
```bash
# Check command availability
foilskybugs --help

# Health check
foilskybugs health

# Database test
foilskybugs db init

# Service status (if installed as service)
sudo ./start.sh --status
```

## 🔄 Upgrading

### System Installation
```bash
cd FoilSkyBugs
git pull origin main
sudo ./install.sh
sudo ./start.sh --restart
```

### Development Installation
```bash
git pull origin main
pip install -e . --upgrade
foilskybugs db migrate  # Run any new database migrations
```

## 🗑️ Uninstallation

### Remove System Installation
```bash
# Stop services
sudo ./start.sh --stop

# Disable services
sudo systemctl disable foilskybugs foilskybugs-web

# Remove service files
sudo rm /etc/systemd/system/foilskybugs*.service
sudo systemctl daemon-reload

# Remove directories (optional - removes all data)
sudo rm -rf /opt/foilskybugs
sudo rm -rf /etc/foilskybugs
sudo rm -rf /var/lib/foilskybugs
sudo rm -rf /var/log/foilskybugs

# Remove user
sudo userdel foilskybugs

# Remove system command
sudo rm /usr/local/bin/foilskybugs
```

### Remove Development Installation
```bash
pip uninstall foilskybugs
```

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/SpaceTrucker2196/FoilSkyBugs/issues)
- **Documentation:** [README.md](README.md)
- **Configuration:** See example configuration files in `config/`