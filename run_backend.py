#!/usr/bin/env python
"""
Backend startup script - Run FastAPI with Uvicorn
Execute from project root: python run_backend.py
"""
import subprocess
import sys
import os

# Ensure we're running from the project root
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)

# Set PYTHONPATH environment variable so uvicorn subprocess can find modules
env = os.environ.copy()
env['PYTHONPATH'] = project_root

# Run uvicorn
if __name__ == "__main__":
    print("Starting FastAPI backend server...")
    print(f"Project root: {project_root}")
    print("API will be available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("-" * 50)
    subprocess.run([
        sys.executable,
        "-m",
        "uvicorn",
        "src.api.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
    ], env=env)
