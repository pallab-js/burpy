"""
Burpy - CLI-based Web Security Testing Tool
"""

import os
import warnings
import urllib3

os.environ['PYTHONWARNINGS'] = 'ignore'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', category=Warning)

__version__ = "1.1.0"
__author__ = "Burpy Team"
__description__ = "A lightweight CLI-based web security testing tool"