"""
Setup script for FoilSkyBugs - ADSB Data Logger & Analytics Platform.
"""

from setuptools import setup, find_packages
import os

# Read README file
def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "FoilSkyBugs - ADSB Data Logger & Analytics Platform"

# Read requirements from requirements.txt
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return []

setup(
    name="foilskybugs",
    version="1.0.0",
    description="Advanced ADSB Data Logger & Analytics Platform",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="SpaceTrucker2196",
    author_email="foilskybugs@example.com",
    url="https://github.com/SpaceTrucker2196/FoilSkyBugs",
    license="MIT",
    
    # Package configuration
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    
    # Dependencies
    install_requires=[
        "pyyaml>=6.0.1",
        "requests>=2.26.0",
        "pydantic>=2.0.0",
        "sqlalchemy>=2.0.0",
        "click>=8.1.0",
        "flask>=3.0.0",
        "flask-cors>=4.0.0",
    ],
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.0.0",
            "black>=23.12.0",
            "flake8>=6.1.0",
            "mypy>=1.8.0",
        ],
        "postgres": [
            "psycopg2-binary>=2.9.5",
        ],
        "rich": [
            "rich>=13.0.0",
        ],
        "rtlsdr": [
            "pyrtlsdr>=0.2.92",
        ],
        "analysis": [
            "numpy>=1.24.0",
            "pandas>=2.1.0",
            "geopy>=2.4.0",
            "shapely>=2.0.0",
        ],
    },
    
    # Entry points for command line tools
    entry_points={
        "console_scripts": [
            "foilskybugs=foilskybugs.cli.main:cli",
        ],
    },
    
    # Package data
    include_package_data=True,
    package_data={
        "foilskybugs": [
            "web/templates/*.html",
            "web/static/*",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
        "Topic :: System :: Monitoring",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    
    # Keywords
    keywords="adsb aviation aircraft tracking sdr rtl-sdr dump1090 mode-s",
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/SpaceTrucker2196/FoilSkyBugs/issues",
        "Source": "https://github.com/SpaceTrucker2196/FoilSkyBugs",
        "Documentation": "https://github.com/SpaceTrucker2196/FoilSkyBugs#readme",
    },
)