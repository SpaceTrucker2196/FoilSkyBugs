"""
Integration tests for system installation and service management.
"""

import pytest
import subprocess
import tempfile
import os
import shutil
from pathlib import Path


class TestSystemInstall:
    """Test system installation and service management."""
    
    @pytest.fixture
    def temp_install_dir(self):
        """Create temporary installation directory."""
        temp_dir = tempfile.mkdtemp(prefix='foilskybugs_test_')
        yield temp_dir
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    def test_install_script_exists(self):
        """Test that install.sh script exists and is executable."""
        script_path = Path(__file__).parent.parent.parent / "install.sh"
        
        assert script_path.exists(), "install.sh script should exist"
        assert os.access(script_path, os.X_OK), "install.sh should be executable"
        
        # Check script content
        with open(script_path, 'r') as f:
            content = f.read()
            assert "FoilSkyBugs Installation Script" in content
            assert "systemctl" in content
            assert "foilskybugs" in content
    
    def test_start_script_exists(self):
        """Test that start.sh script exists and is executable."""
        script_path = Path(__file__).parent.parent.parent / "start.sh"
        
        assert script_path.exists(), "start.sh script should exist"
        assert os.access(script_path, os.X_OK), "start.sh should be executable"
        
        # Check script content
        with open(script_path, 'r') as f:
            content = f.read()
            assert "FoilSkyBugs Service Starter" in content
            assert "systemctl" in content
            assert "--status" in content
    
    def test_install_script_help(self):
        """Test install script shows proper usage when not run as root."""
        script_path = Path(__file__).parent.parent.parent / "install.sh"
        
        # Run script without root privileges (should show error)
        result = subprocess.run(
            [str(script_path)], 
            capture_output=True, 
            text=True
        )
        
        # Should exit with error code 1 (not root)
        assert result.returncode == 1
        assert "must be run as root" in result.stdout
    
    def test_start_script_help(self):
        """Test start script shows help message."""
        script_path = Path(__file__).parent.parent.parent / "start.sh"
        
        # Test help option
        result = subprocess.run(
            [str(script_path), "--help"], 
            capture_output=True, 
            text=True
        )
        
        # Should show help and exit cleanly
        assert result.returncode == 0
        assert "FoilSkyBugs Service Management" in result.stdout
        assert "--web-only" in result.stdout
        assert "--data-only" in result.stdout
        assert "--status" in result.stdout
    
    def test_start_script_non_root_error(self):
        """Test start script shows error when not run as root."""
        script_path = Path(__file__).parent.parent.parent / "start.sh"
        
        # Run script without root privileges (should show error)
        result = subprocess.run(
            [str(script_path)], 
            capture_output=True, 
            text=True
        )
        
        # Should exit with error code 1 (not root)
        assert result.returncode == 1
        assert "must be run as root" in result.stdout
    
    def test_config_validation(self):
        """Test configuration file validation."""
        from src.foilskybugs.core.config import Config
        
        # Test default configuration loads without errors
        config = Config()
        assert config.app_name == "FoilSkyBugs"
        assert config.database.url is not None
        assert config.web.port == 8080
    
    def test_config_file_creation(self, temp_install_dir):
        """Test configuration file creation with proper format."""
        from src.foilskybugs.core.config import Config
        import yaml
        
        # Create a test config file
        config_path = os.path.join(temp_install_dir, "test_config.yaml")
        
        config_data = {
            'app': {
                'name': 'FoilSkyBugs',
                'version': '1.0.0',
                'environment': 'production'
            },
            'database': {
                'url': f'sqlite:///{temp_install_dir}/test.db'
            },
            'web': {
                'host': '0.0.0.0',
                'port': 8080,
                'debug': False
            },
            'logging': {
                'level': 'INFO',
                'file': f'{temp_install_dir}/test.log'
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        # Test loading the config
        config = Config.from_file(config_path)
        assert config.app_name == "FoilSkyBugs"
        assert config.environment == "production"
        assert temp_install_dir in config.database.url
    
    def test_service_command_availability(self):
        """Test that foilskybugs command is available after installation."""
        # This test assumes the package is properly installed
        result = subprocess.run(
            ["foilskybugs", "--help"], 
            capture_output=True, 
            text=True
        )
        
        assert result.returncode == 0
        assert "FoilSkyBugs - ADSB Data Logger" in result.stdout
        assert "Commands:" in result.stdout
    
    def test_health_check_command(self):
        """Test health check command functionality."""
        result = subprocess.run(
            ["foilskybugs", "health"], 
            capture_output=True, 
            text=True
        )
        
        # Health check should run (may show degraded status without services)
        assert result.returncode in [0, 1]  # 0 for healthy, 1 for degraded
        assert "Overall Status:" in result.stdout
        assert "Component Status:" in result.stdout
    
    def test_database_init_command(self):
        """Test database initialization command."""
        result = subprocess.run(
            ["foilskybugs", "db", "init"], 
            capture_output=True, 
            text=True
        )
        
        # Database init should succeed
        assert result.returncode == 0
        assert "Database initialized successfully" in result.stdout or "already" in result.stdout.lower()
    
    def test_systemd_service_files_format(self):
        """Test that systemd service files are properly formatted."""
        install_script = Path(__file__).parent.parent.parent / "install.sh"
        
        with open(install_script, 'r') as f:
            content = f.read()
        
        # Check that service file creation includes required sections
        assert "[Unit]" in content
        assert "[Service]" in content
        assert "[Install]" in content
        assert "ExecStart=" in content
        assert "User=" in content
        assert "WantedBy=multi-user.target" in content
    
    def test_security_settings_in_service(self):
        """Test that security settings are included in systemd service."""
        install_script = Path(__file__).parent.parent.parent / "install.sh"
        
        with open(install_script, 'r') as f:
            content = f.read()
        
        # Check security hardening options
        assert "NoNewPrivileges=true" in content
        assert "ProtectSystem=strict" in content
        assert "ProtectHome=true" in content
        assert "PrivateDevices=true" in content
    
    def test_start_script_options(self):
        """Test start script handles different options correctly."""
        script_path = Path(__file__).parent.parent.parent / "start.sh"
        
        # Test invalid option
        result = subprocess.run(
            [str(script_path), "--invalid-option"], 
            capture_output=True, 
            text=True
        )
        
        assert result.returncode == 1
        assert "Unknown option" in result.stdout
    
    def test_directory_structure_requirements(self):
        """Test that required directories are accounted for in install script."""
        install_script = Path(__file__).parent.parent.parent / "install.sh"
        
        with open(install_script, 'r') as f:
            content = f.read()
        
        # Check that install script creates necessary directories
        required_dirs = [
            "/opt/foilskybugs",
            "/etc/foilskybugs", 
            "/var/log/foilskybugs",
            "/var/lib/foilskybugs"
        ]
        
        for directory in required_dirs:
            assert directory in content, f"Install script should reference {directory}"
    
    def test_user_creation_in_install_script(self):
        """Test that install script properly handles user creation."""
        install_script = Path(__file__).parent.parent.parent / "install.sh"
        
        with open(install_script, 'r') as f:
            content = f.read()
        
        # Check user creation logic
        assert "useradd --system" in content
        assert "SERVICE_USER=" in content
        assert 'if ! id "$SERVICE_USER"' in content
    
    def test_package_installation_in_scripts(self):
        """Test that required packages are installed by install script."""
        install_script = Path(__file__).parent.parent.parent / "install.sh"
        
        with open(install_script, 'r') as f:
            content = f.read()
        
        # Check essential packages
        essential_packages = [
            "python3",
            "python3-pip",
            "python3-venv",
            "build-essential",
            "sqlite3"
        ]
        
        for package in essential_packages:
            assert package in content, f"Install script should install {package}"