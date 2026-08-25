"""
Kafka Real-Time Streaming Module for Environmental Intelligence Pipeline.
"""

import sys
import os

__version__ = "1.0.0"

_current_dir = os.path.normcase(os.path.abspath(os.path.dirname(__file__)))
_parent_dir = os.path.normcase(os.path.abspath(os.path.join(_current_dir, "..")))
