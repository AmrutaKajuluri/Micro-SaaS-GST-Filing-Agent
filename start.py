import subprocess
import sys
import time
import webbrowser
from threading import Thread

def start_api_server():
    """Start the Flask API server"""
    try:
        print("Starting Flask API server...")
        subprocess.run([sys.executable, "api_server.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting API server: {e}")
    except KeyboardInterrupt:
        print("API server stopped")

def start_frontend():
    """Start the React frontend"""
    try:
        print("Starting React frontend...")
        # Change to frontend directory and start npm
        subprocess.run(["npm", "start"], cwd="frontend", check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting frontend: {e}")
    except KeyboardInterrupt:
        print("Frontend stopped")

def main():
    print("🚀 Starting AI GST Filing Agent...")
    print("=" * 50)
    
    # Check if node_modules exists, if not, install dependencies
    import os
    if not os.path.exists("frontend/node_modules"):
        print("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd="frontend", check=True)
    
    # Start API server in a separate thread
    api_thread = Thread(target=start_api_server, daemon=True)
    api_thread.start()
    
    # Wait a bit for API server to start
    time.sleep(3)
    
    # Open browser for frontend
    print("Opening browser...")
    webbrowser.open("http://localhost:3000")
    
    # Start frontend in main thread
    try:
        start_frontend()
    except KeyboardInterrupt:
        print("\n👋 Shutting down AI GST Filing Agent...")
        sys.exit(0)

if __name__ == "__main__":
    main()
