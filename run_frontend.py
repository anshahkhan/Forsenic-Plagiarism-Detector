#!/usr/bin/env python
"""
Frontend startup script - Run Streamlit UI
Execute from project root: python run_frontend.py
"""
import subprocess
import sys
import os

# Ensure we're running from the project root
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)

# Set PYTHONPATH environment variable
env = os.environ.copy()
env['PYTHONPATH'] = project_root

# Run streamlit
if __name__ == "__main__":
    print("Starting Streamlit frontend...")
    print(f"Project root: {project_root}")
    print("UI will be available at: http://localhost:8501")
    print("-" * 50)
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "src/api/main.py"
    ], env=env)
