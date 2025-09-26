"""
Tests for system service status and management.
"""

import pytest
import subprocess
import os
import tempfile
from pathlib import Path


class TestServiceStatus:
    """Test service status checking and management."""
    
    def test_health_command_provides_service_status(self):
        """Test that health command shows service status information."""
        result = subprocess.run(
            ["foilskybugs", "health"], 
            capture_output=True, 
            text=True
        )
        
        # Health check should provide component status
        assert "Component Status:" in result.stdout
        assert "database:" in result.stdout.lower()
        assert "data_collection:" in result.stdout.lower() or "data collection:" in result.stdout.lower()
        assert "decoder:" in result.stdout.lower()
    
    def test_start_script_status_option(self):
        """Test start script --status option functionality."""
        script_path = Path(__file__).parent.parent.parent / "start.sh"
        
        # Test help shows status option
        result = subprocess.run(
            [str(script_path), "--help"], 
            capture_output=True, 
            text=True
        )
        
        assert result.returncode == 0
        assert "--status" in result.stdout
        assert "Show service status" in result.stdout
    
    def test_service_status_command_structure(self):
        """Test that service status commands are properly structured."""
        start_script = Path(__file__).parent.parent.parent / "start.sh"
        
        with open(start_script, 'r') as f:
            content = f.read()
        
        # Check for proper systemctl commands
        assert "systemctl is-active" in content
        assert "systemctl is-enabled" in content
        assert "systemctl status" in content
        
        # Check for service status functions
        assert "get_service_status()" in content
        assert "show_status()" in content
    
    def test_service_management_commands(self):
        """Test that service management commands are available."""
        start_script = Path(__file__).parent.parent.parent / "start.sh"
        
        with open(start_script, 'r') as f:
            content = f.read()
        
        # Check for all required service management operations
        service_operations = [
            "systemctl start",
            "systemctl stop", 
            "systemctl restart",
            "systemctl status"
        ]
        
        for operation in service_operations:
            assert operation in content, f"Script should support {operation}"
    
    def test_log_viewing_functionality(self):
        """Test that log viewing functionality is available."""
        start_script = Path(__file__).parent.parent.parent / "start.sh"
        
        with open(start_script, 'r') as f:
            content = f.read()
        
        # Check for journalctl commands
        assert "journalctl -u" in content
        assert "show_logs()" in content
        assert "--logs" in content
    
    def test_config_validation_in_health_check(self):
        """Test that health check validates configuration."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
app:
  name: "FoilSkyBugs"
  version: "1.0.0"

database:
  url: "sqlite:///test.db"

web:
  host: "127.0.0.1"
  port: 8080
""")
            temp_config = f.name
        
        try:
            result = subprocess.run(
                ["foilskybugs", "health", "--config", temp_config], 
                capture_output=True, 
                text=True
            )
            
            # Should successfully run with custom config
            assert "Overall Status:" in result.stdout
            
        finally:
            # Cleanup
            if os.path.exists(temp_config):
                os.unlink(temp_config)
    
    def test_stats_command_availability(self):
        """Test that stats command is available for monitoring."""
        result = subprocess.run(
            ["foilskybugs", "stats", "--help"], 
            capture_output=True, 
            text=True
        )
        
        assert result.returncode == 0
        assert "statistics" in result.stdout.lower()
        assert "--last-hour" in result.stdout
    
    def test_web_service_availability_check(self):
        """Test checking web service availability."""
        start_script = Path(__file__).parent.parent.parent / "start.sh"
        
        with open(start_script, 'r') as f:
            content = f.read()
        
        # Check for web service management
        assert "${SERVICE_NAME}-web" in content or "foilskybugs-web" in content
        assert "--web-only" in content
        assert "Web service" in content
    
    def test_service_dependency_handling(self):
        """Test that service dependencies are properly handled."""
        install_script = Path(__file__).parent.parent.parent / "install.sh"
        
        with open(install_script, 'r') as f:
            content = f.read()
        
        # Check systemd service dependencies
        assert "After=network.target" in content
        assert "Wants=network.target" in content
    
    def test_error_handling_in_scripts(self):
        """Test that scripts have proper error handling."""
        start_script = Path(__file__).parent.parent.parent / "start.sh"
        
        with open(start_script, 'r') as f:
            content = f.read()
        
        # Check for error handling
        assert "set -e" in content  # Exit on error
        assert "|| echo" in content or "|| true" in content  # Error handling
        
        install_script = Path(__file__).parent.parent.parent / "install.sh"
        
        with open(install_script, 'r') as f:
            content = f.read()
        
        assert "set -e" in content  # Exit on error
    
    def test_service_restart_functionality(self):
        """Test service restart functionality in start script."""
        start_script = Path(__file__).parent.parent.parent / "start.sh"
        
        with open(start_script, 'r') as f:
            content = f.read()
        
        # Check restart functionality
        assert "--restart" in content
        assert "systemctl restart" in content
        assert "RESTART_SERVICES" in content
    
    def test_service_stop_functionality(self):
        """Test service stop functionality in start script."""
        start_script = Path(__file__).parent.parent.parent / "start.sh"
        
        with open(start_script, 'r') as f:
            content = f.read()
        
        # Check stop functionality
        assert "--stop" in content
        assert "systemctl stop" in content
        assert "STOP_SERVICES" in content
    
    def test_database_initialization_check(self):
        """Test that database initialization is checked before starting services."""
        start_script = Path(__file__).parent.parent.parent / "start.sh"
        
        with open(start_script, 'r') as f:
            content = f.read()
        
        # Check database initialization
        assert "foilskybugs db init" in content
        assert "Initializing database" in content
    
    def test_configuration_file_validation(self):
        """Test that configuration file is validated."""
        start_script = Path(__file__).parent.parent.parent / "start.sh"
        
        with open(start_script, 'r') as f:
            content = f.read()
        
        # Check config file handling
        assert "CONFIG_FILE=" in content
        assert "/etc/foilskybugs/config.yaml" in content
        assert "-f \"$CONFIG_FILE\"" in content or "[ -f" in content
    
    def test_multiple_service_handling(self):
        """Test that script can handle multiple services."""
        start_script = Path(__file__).parent.parent.parent / "start.sh"
        
        with open(start_script, 'r') as f:
            content = f.read()
        
        # Check for handling both data and web services
        assert "DATA_ONLY" in content
        assert "WEB_ONLY" in content
        assert "service_exists()" in content