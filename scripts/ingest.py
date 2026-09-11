#!/usr/bin/env python3
"""
ConvergenceTerminal Ingest Dispatcher
Delegates to internal/scripts/ingest.py
"""
import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INTERNAL_INGEST = os.path.join(os.path.dirname(SCRIPT_DIR), "internal", "scripts", "ingest.py")

if __name__ == "__main__":
    cmd = [sys.executable, INTERNAL_INGEST] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))

