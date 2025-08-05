#!/usr/bin/env python3
"""
Simple runner script for SASB KPI Generator
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and run the main function
from sasb_kpi_generator.main import main

if __name__ == "__main__":
    main() 