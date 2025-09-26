#!/bin/bash
# FoilSkyBugs Start Script
# This script starts the database and FoilSkyBugs services

set -e  # Exit on any error

SERVICE_NAME="foilskybugs"
CONFIG_FILE="/etc/foilskybugs/config.yaml"

echo "🛩️  FoilSkyBugs Service Starter"
echo "==============================="

# Parse command line arguments first to handle help and invalid options
SHOW_HELP=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            SHOW_HELP=true
            break
            ;;
        --web-only|--data-only|--status|--stop|--restart|--logs)
            # Valid options, continue processing after root check
            break
            ;;
        -*)
            echo "❌ Unknown option: $1"
            echo "   Use --help for usage information"
            exit 1
            ;;
        *)
            break
            ;;
    esac
done

# Show help without requiring root
if [[ "$SHOW_HELP" == "true" ]]; then
    echo "FoilSkyBugs Service Management"
    echo ""
    echo "Usage: sudo $0 [options]"
    echo ""
    echo "Options:"
    echo "  --web-only     Start only the web interface"
    echo "  --data-only    Start only the data collection service"
    echo "  --status       Show service status"
    echo "  --stop         Stop all services"
    echo "  --restart      Restart all services"
    echo "  --logs         Show service logs"
    echo "  --help, -h     Show this help message"
    echo ""
    echo "Examples:"
    echo "  sudo $0                    # Start all services"
    echo "  sudo $0 --web-only        # Start only web interface"
    echo "  sudo $0 --status          # Check service status"
    echo "  sudo $0 --logs             # View logs"
    exit 0
fi

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
    echo "❌ This script must be run as root (use sudo)"
    echo "   Usage: sudo ./start.sh [options]"
    echo ""
    echo "   Options:"
    echo "     --web-only    Start only the web interface"
    echo "     --data-only   Start only the data collection service"
    echo "     --status      Show service status"
    echo "     --stop        Stop all services"
    echo "     --restart     Restart all services"
    echo "     --logs        Show service logs"
    exit 1
fi

# Reset positional parameters and parse again
# Reset positional parameters and parse again
set -- "$@"  # Reset arguments
WEB_ONLY=false
DATA_ONLY=false
SHOW_STATUS=false
STOP_SERVICES=false
RESTART_SERVICES=false
SHOW_LOGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --web-only)
            WEB_ONLY=true
            shift
            ;;
        --data-only)
            DATA_ONLY=true
            shift
            ;;
        --status)
            SHOW_STATUS=true
            shift
            ;;
        --stop)
            STOP_SERVICES=true
            shift
            ;;
        --restart)
            RESTART_SERVICES=true
            shift
            ;;
        --logs)
            SHOW_LOGS=true
            shift
            ;;
        --help|-h)
            # Already handled above
            shift
            ;;
        *)
            # Skip unknown arguments (already handled above)
            shift
            ;;
    esac
done

# Function to check if service exists
service_exists() {
    systemctl list-unit-files | grep -q "^$1.service"
}

# Function to get service status
get_service_status() {
    if service_exists "$1"; then
        if systemctl is-active --quiet "$1"; then
            echo "🟢 RUNNING"
        elif systemctl is-enabled --quiet "$1"; then
            echo "🟡 STOPPED (enabled)"
        else
            echo "🔴 STOPPED (disabled)"
        fi
    else
        echo "❌ NOT INSTALLED"
    fi
}

# Function to show status
show_status() {
    echo "📊 Service Status:"
    echo "   Data Service: $(get_service_status "$SERVICE_NAME")"
    echo "   Web Service:  $(get_service_status "${SERVICE_NAME}-web")"
    echo ""
    
    # Show detailed status if services exist
    if service_exists "$SERVICE_NAME"; then
        echo "📋 Detailed Status:"
        systemctl status "$SERVICE_NAME" --no-pager -l || true
        echo ""
    fi
    
    if service_exists "${SERVICE_NAME}-web"; then
        systemctl status "${SERVICE_NAME}-web" --no-pager -l || true
        echo ""
    fi
    
    # Show health check if command is available
    if command -v foilskybugs &> /dev/null; then
        echo "🔍 Health Check:"
        if [[ -f "$CONFIG_FILE" ]]; then
            foilskybugs health --config "$CONFIG_FILE" || echo "   Health check failed or service not running"
        else
            foilskybugs health || echo "   Health check failed or service not running"
        fi
    fi
}

# Function to show logs
show_logs() {
    echo "📜 Recent Service Logs:"
    echo "======================="
    
    if service_exists "$SERVICE_NAME"; then
        echo ""
        echo "🔧 Data Service Logs (last 20 lines):"
        journalctl -u "$SERVICE_NAME" -n 20 --no-pager || true
    fi
    
    if service_exists "${SERVICE_NAME}-web"; then
        echo ""
        echo "🌐 Web Service Logs (last 20 lines):"
        journalctl -u "${SERVICE_NAME}-web" -n 20 --no-pager || true
    fi
    
    echo ""
    echo "📊 To follow logs in real-time:"
    echo "   journalctl -u $SERVICE_NAME -f"
    echo "   journalctl -u ${SERVICE_NAME}-web -f"
}

# Handle different modes
if [[ "$SHOW_STATUS" == "true" ]]; then
    show_status
    exit 0
fi

if [[ "$SHOW_LOGS" == "true" ]]; then
    show_logs
    exit 0
fi

if [[ "$STOP_SERVICES" == "true" ]]; then
    echo "🛑 Stopping FoilSkyBugs services..."
    
    if service_exists "${SERVICE_NAME}-web"; then
        systemctl stop "${SERVICE_NAME}-web" || echo "   Web service was not running"
        echo "✓ Web service stopped"
    fi
    
    if service_exists "$SERVICE_NAME"; then
        systemctl stop "$SERVICE_NAME" || echo "   Data service was not running"
        echo "✓ Data service stopped"
    fi
    
    echo "✅ All services stopped"
    exit 0
fi

if [[ "$RESTART_SERVICES" == "true" ]]; then
    echo "🔄 Restarting FoilSkyBugs services..."
    
    if service_exists "$SERVICE_NAME" && ! [[ "$WEB_ONLY" == "true" ]]; then
        systemctl restart "$SERVICE_NAME"
        echo "✓ Data service restarted"
    fi
    
    if service_exists "${SERVICE_NAME}-web" && ! [[ "$DATA_ONLY" == "true" ]]; then
        systemctl restart "${SERVICE_NAME}-web"
        echo "✓ Web service restarted"
    fi
    
    echo "✅ Services restarted"
    show_status
    exit 0
fi

# Check if services are installed
if ! service_exists "$SERVICE_NAME" && ! service_exists "${SERVICE_NAME}-web"; then
    echo "❌ FoilSkyBugs services not found!"
    echo "   Please run the installation script first: sudo ./install.sh"
    exit 1
fi

# Start services
echo "🚀 Starting FoilSkyBugs services..."

# Initialize database if needed
if [[ -f "$CONFIG_FILE" ]] && command -v foilskybugs &> /dev/null; then
    echo "🗄️  Initializing database..."
    sudo -u foilskybugs foilskybugs db init --config "$CONFIG_FILE" 2>/dev/null || echo "   Database already initialized or unavailable"
fi

# Start data service
if service_exists "$SERVICE_NAME" && ! [[ "$WEB_ONLY" == "true" ]]; then
    echo "🔧 Starting data collection service..."
    systemctl start "$SERVICE_NAME"
    sleep 2
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "✅ Data service started successfully"
    else
        echo "❌ Failed to start data service"
        echo "   Check logs: journalctl -u $SERVICE_NAME"
        exit 1
    fi
fi

# Start web service
if service_exists "${SERVICE_NAME}-web" && ! [[ "$DATA_ONLY" == "true" ]]; then
    echo "🌐 Starting web interface..."
    systemctl start "${SERVICE_NAME}-web"
    sleep 2
    
    if systemctl is-active --quiet "${SERVICE_NAME}-web"; then
        echo "✅ Web service started successfully"
        echo "   🌐 Access the dashboard at: http://localhost:8080"
    else
        echo "❌ Failed to start web service"
        echo "   Check logs: journalctl -u ${SERVICE_NAME}-web"
        exit 1
    fi
fi

echo ""
echo "🎉 FoilSkyBugs is now running!"
echo ""
show_status

echo ""
echo "📋 Useful commands:"
echo "   • Check status: sudo $0 --status"
echo "   • View logs:    sudo $0 --logs"
echo "   • Stop:         sudo $0 --stop"
echo "   • Restart:      sudo $0 --restart"
echo "   • Health check: foilskybugs health"