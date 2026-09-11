#!/usr/bin/env python3
"""
ConvergenceTerminal Synthesize Dispatcher
Delegates to internal/scripts/synthesize.py — that module is the
single canonical source of truth for all synthesis logic.

Pattern mirrors scripts/ingest.py.
"""
import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INTERNAL_SYNTHESIZE = os.path.join(
    os.path.dirname(SCRIPT_DIR), "internal", "scripts", "synthesize.py"
)

if __name__ == "__main__":
    cmd = [sys.executable, INTERNAL_SYNTHESIZE] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))
