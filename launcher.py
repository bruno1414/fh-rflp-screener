#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""launcher.py

This script acts as a launcher for the FH RFLP Screener web application.
It starts the Flask development server and automatically opens a web browser
to the application's URL once the server is ready.
"""

import threading
import webbrowser
import time
import sys
import os

# Add the project root directory to the Python system path.
# This ensures that modules within the project (e.g., 'app') can be imported correctly.
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

def open_browser():
    """Waits for a short period to allow the server to start, then opens the default web browser to the application's URL."""
    time.sleep(2)  # Give the Flask server a moment to initialize.
    webbrowser.open("http://localhost:5000") # Open the application in the default web browser.

def main():
    """Main function to create the Flask app, start the browser thread, and run the application server."""
    app = create_app()
    
    # Start a new thread to open the web browser.
    # daemon=True ensures that the thread will not prevent the main program from exiting.
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("Starting FH RFLP Screener...")
    # Run the Flask application.
    # port=5000 specifies the port the application will listen on.
    # debug=False disables debug mode for a more stable production-like environment.
    # use_reloader=False prevents the server from restarting automatically on code changes,
    # which is suitable for a launcher script that starts once.
    app.run(port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Entry point for the script execution.
    main()
