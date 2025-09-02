#!/usr/bin/env python3
"""
Simple Microphone Test - Quick test for audio input
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.testing.microphone_test import main

if __name__ == '__main__':
    main()
