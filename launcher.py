"""
Baseball Binder Application Launcher
Starts the FastAPI server and opens the browser automatically.
"""
import sys
import os
import time
import webbrowser
import threading
import uvicorn
from pathlib import Path

def open_browser():
    """Open browser after a short delay to ensure server is running"""
    time.sleep(2)
    webbrowser.open('http://localhost:8000')

def main():
    """Main launcher function"""
    print("=" * 60)
    print("  Baseball Binder - Card Collection Manager")
    print("=" * 60)
    print()
    print("Starting server...")
    print("The application will open in your browser shortly.")
    print()
    print("To stop the application, close this window or press Ctrl+C")
    print("=" * 60)
    print()

    # Start browser opener in separate thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Start the FastAPI server
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=False
        )
    except KeyboardInterrupt:
        print("\n\nShutting down Baseball Binder...")
        print("Thank you for using Baseball Binder!")
        sys.exit(0)

if __name__ == "__main__":
    main()
