#!/usr/bin/env python3
"""
Local development runner script for CareLens 360.
This script helps set up and run the application locally.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables."""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found!")
        print("📝 Creating .env from .env.example...")
        env_example = Path(".env.example")
        if env_example.exists():
            env_file.write_text(env_example.read_text())
            print("✅ Created .env file. Please update it with your credentials.")
            return False
        else:
            print("❌ .env.example not found. Please create .env manually.")
            return False
    
    # Check for required variables
    env_content = env_file.read_text()
    required_vars = ["GCP_PROJECT_ID", "GCS_BUCKET_NAME", "GEMINI_API_KEY"]
    missing = []
    
    for var in required_vars:
        if f"{var}=" not in env_content or f"{var}=\n" in env_content or f"{var}=" in env_content.split("\n")[0]:
            # Check if it's actually set (not empty)
            lines = env_content.split("\n")
            for line in lines:
                if line.startswith(f"{var}="):
                    value = line.split("=", 1)[1].strip()
                    if not value or value == "your-project-id" or value == "your-bucket-name" or value == "your-gemini-api-key":
                        missing.append(var)
                    break
            else:
                missing.append(var)
    
    if missing:
        print(f"⚠️  Missing or empty required environment variables: {', '.join(missing)}")
        print("📝 Please update your .env file with the required values.")
        return False
    
    return True

def check_dependencies():
    """Check if required Python packages are installed."""
    try:
        import streamlit
        import google.cloud.storage
        import google.cloud.firestore
        import google.generativeai
        import PIL
        import dotenv
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("📦 Installing dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies. Please run: pip install -r requirements.txt")
            return False

def main():
    """Main function to run the application."""
    print("🚀 Starting CareLens 360...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment file
    if not check_env_file():
        print("\n⚠️  Please configure your .env file before running the application.")
        sys.exit(1)
    
    # Run Streamlit
    print("\n✅ All checks passed!")
    print("🌐 Starting Streamlit application...")
    print("=" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "src/app.py",
            "--server.headless", "true"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down CareLens 360...")
        sys.exit(0)

if __name__ == "__main__":
    main()

