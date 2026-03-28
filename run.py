#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""run.py

This script serves as the primary entry point for the FH RFLP Screener web application.
It initializes the Flask application and runs the development server.
"""

from app import create_app

# Create the Flask application instance by calling the factory function from the 'app' package.
# This allows for flexible application configuration and testing.
app = create_app()

if __name__ == "__main__":
    # This block ensures the development server only runs when the script is executed directly.
    print("Starting FH RFLP Screener...")
    print("Open your browser and go to: http://localhost:5000")
    # Run the Flask application.
    # debug=True enables debug mode, providing a debugger and auto-reloader for development.
    # port=5000 specifies that the application will listen on port 5000.
    app.run(debug=True, port=5000)
