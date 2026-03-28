#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""wsgi.py

This script provides the WSGI (Web Server Gateway Interface) entry point for the FH RFLP Screener application.
It is used by WSGI-compatible web servers (like Gunicorn, uWSGI) to serve the Flask application in a production environment.
"""

from app import create_app

# Create the Flask application instance.
# This calls the factory function from the 'app' package, which sets up the application.
app = create_app()

if __name__ == "__main__":
    # This block is primarily for local testing or development purposes.
    # In a production WSGI environment, the web server directly imports 'app' and runs it.
    app.run()
