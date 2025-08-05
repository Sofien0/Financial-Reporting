#!/usr/bin/env python3
"""
Runner script for SASB Topics Scraper
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import and run the scraper
from scripts.scrape_sasb_topics import main

if __name__ == "__main__":
    main() 