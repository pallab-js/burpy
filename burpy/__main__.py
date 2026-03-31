#!/usr/bin/env python3
"""
Burpy main entry point - Run with suppressed warnings
"""

import sys
import warnings

# Suppress ALL warnings before any imports
warnings.filterwarnings('ignore')
try:
    import urllib3
    urllib3.disable_warnings()
except:
    pass

# Now import and run
from burpy.cli.main import cli

if __name__ == '__main__':
    sys.exit(cli())