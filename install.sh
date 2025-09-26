#!/bin/bash
# FoilSkyBugs Installation Script
# This script installs FoilSkyBugs as a system-wide command and service

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="foilskybugs"
SERVICE_USER="foilskybugs"
INSTALL_DIR="/opt/foilskybugs"
CONFIG_DIR="/etc/foilskybugs"
LOG_DIR="/var/log/foilskybugs"
DATA_DIR="/var/lib/foilskybugs"

echo "🛩️  FoilSkyBugs Installation Script"
echo "=================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Check if running on Debian/Ubuntu
if ! command -v apt &> /dev/null; then
    echo "❌ This script is designed for Debian/Ubuntu systems"
    exit 1
fi

echo "📦 Installing system dependencies..."
apt update
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    pkg-config \
    libffi-dev \
    libssl-dev \
    git \
    sqlite3 \
    libsqlite3-dev

# Optional: Install PostgreSQL support
if [[ "${1:-}" == "--with-postgresql" ]]; then
    echo "🐘 Installing PostgreSQL support..."
    apt install -y postgresql postgresql-contrib libpq-dev
fi

# Optional: Install RTL-SDR support
if [[ "${1:-}" == "--with-rtlsdr" || "${2:-}" == "--with-rtlsdr" ]]; then
    echo "📻 Installing RTL-SDR support..."
    apt install -y librtlsdr-dev rtl-sdr
fi

echo "👤 Creating system user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --shell /bin/false --home "$INSTALL_DIR" --create-home "$SERVICE_USER"
    echo "✓ Created user: $SERVICE_USER"
else
    echo "✓ User already exists: $SERVICE_USER"
fi

echo "📁 Creating directories..."
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR" "$DATA_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR" "$LOG_DIR" "$DATA_DIR"
chmod 755 "$CONFIG_DIR"

echo "🔧 Installing FoilSkyBugs..."
# Copy source code to installation directory
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Create Python virtual environment
sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"

# Install FoilSkyBugs in the virtual environment
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip setuptools wheel
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -e "$INSTALL_DIR"

# Create system-wide symlink
ln -sf "$INSTALL_DIR/venv/bin/foilskybugs" /usr/local/bin/foilskybugs
echo "✓ Created system-wide command: /usr/local/bin/foilskybugs"

echo "⚙️  Setting up configuration..."
if [[ -f "$SCRIPT_DIR/config/config.example.yaml" ]]; then
    cp "$SCRIPT_DIR/config/config.example.yaml" "$CONFIG_DIR/config.yaml"
    # Update paths in config
    sed -i "s|sqlite:///foilskybugs.db|sqlite:///$DATA_DIR/foilskybugs.db|g" "$CONFIG_DIR/config.yaml"
    sed -i "s|foilskybugs.log|$LOG_DIR/foilskybugs.log|g" "$CONFIG_DIR/config.yaml"
    chown "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR/config.yaml"
    echo "✓ Created configuration: $CONFIG_DIR/config.yaml"
else
    echo "⚠️  Configuration example not found, creating minimal config..."
    cat > "$CONFIG_DIR/config.yaml" << EOF
app:
  name: "FoilSkyBugs"
  version: "1.0.0"
  environment: "production"

database:
  url: "sqlite:///$DATA_DIR/foilskybugs.db"

web:
  host: "0.0.0.0"
  port: 8080
  debug: false

logging:
  level: "INFO"
  file: "$LOG_DIR/foilskybugs.log"
EOF
    chown "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR/config.yaml"
fi

echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=FoilSkyBugs ADSB Data Logger & Analytics Platform
Documentation=https://github.com/SpaceTrucker2196/FoilSkyBugs
After=network.target
Wants=network.target

[Service]
Type=forking
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$INSTALL_DIR/src
ExecStartPre=$INSTALL_DIR/venv/bin/foilskybugs db init --config $CONFIG_DIR/config.yaml
ExecStart=$INSTALL_DIR/venv/bin/foilskybugs start --config $CONFIG_DIR/config.yaml
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR $LOG_DIR
PrivateDevices=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
EOF

echo "🔧 Creating web service..."
cat > /etc/systemd/system/${SERVICE_NAME}-web.service << EOF
[Unit]
Description=FoilSkyBugs Web Interface
Documentation=https://github.com/SpaceTrucker2196/FoilSkyBugs
After=network.target ${SERVICE_NAME}.service
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$INSTALL_DIR/src
ExecStart=$INSTALL_DIR/venv/bin/foilskybugs web --config $CONFIG_DIR/config.yaml
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR $LOG_DIR
PrivateDevices=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl enable ${SERVICE_NAME}-web

echo "📊 Initializing database..."
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/foilskybugs" db init --config "$CONFIG_DIR/config.yaml"

echo "✅ Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "   • Configure: Edit $CONFIG_DIR/config.yaml"
echo "   • Start services: systemctl start $SERVICE_NAME $SERVICE_NAME-web"
echo "   • Check status: systemctl status $SERVICE_NAME"
echo "   • View logs: journalctl -u $SERVICE_NAME -f"
echo "   • Web interface: http://localhost:8080"
echo "   • Command-line: foilskybugs --help"
echo ""
echo "🔧 Service management:"
echo "   • Start:   systemctl start $SERVICE_NAME"
echo "   • Stop:    systemctl stop $SERVICE_NAME"
echo "   • Restart: systemctl restart $SERVICE_NAME"
echo "   • Status:  systemctl status $SERVICE_NAME"
echo ""
echo "🌐 Web interface:"
echo "   • Start:   systemctl start $SERVICE_NAME-web"
echo "   • URL:     http://localhost:8080"