import threading
import webbrowser
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

def open_browser():
    """Wait for server to start then open browser."""
    time.sleep(2)
    webbrowser.open("http://localhost:5000")

def main():
    app = create_app()
    
    # Open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("Starting FH RFLP Screener...")
    app.run(port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    main()