#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""app/__init__.py

This file initializes the Flask application for the FH RFLP Screener.
It sets up the application configuration, registers blueprints, and defines the factory function to create the app instance.
"""

from flask import Flask

def create_app():
    """Creates and configures the Flask application instance.

    This factory function is responsible for:
    1. Initializing the Flask app.
    2. Setting up template and static file folders.
    3. Configuring a secret key for session management.
    4. Registering application blueprints (e.g., routes).

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__, 
                template_folder="templates", # Specifies the directory for HTML templates.
                static_folder="static")    # Specifies the directory for static assets like CSS, JS, images.
    
    # Set a secret key for the application.
    # This is crucial for security, used for signing session cookies and other security-related needs.
    # In a production environment, this should be loaded from an environment variable or a secure configuration.
    app.secret_key = "fh-rflp-screening-2026"
    
    # Register blueprints.
    # Blueprints are a way to organize Flask applications into smaller, reusable components.
    # The 'main' blueprint likely contains the primary routes and views of the application.
    from app.routes import main
    app.register_blueprint(main)
    
    return app
