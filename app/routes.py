#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""app/routes.py

This module defines the web routes and API endpoints for the FH RFLP Screener Flask application.
It handles requests for displaying web pages and serving data through a RESTful API.
"""

from flask import Blueprint, render_template, request, jsonify
from app.core.panel import (
    get_panel_summary,   # Function to retrieve a summary of the RFLP panel.
    search_panel,        # Function to search the RFLP panel.
    get_mutation_detail  # Function to get detailed information about a specific mutation.
)
from app.core.pipeline import run_full_analysis # Function to run the complete RFLP analysis pipeline.

# Create a Blueprint for the main application routes.
# Blueprints help organize routes and other application components into modular units.
main = Blueprint("main", __name__)


# ── Pages ─────────────────────────────────────────────────────

@main.route("/")
def index():
    """Renders the home page of the application.

    This route serves the main landing page, typically providing an overview
    or entry points to other sections of the application.
    """
    return render_template("index.html")


@main.route("/panel")
def panel():
    """Renders the page displaying the pre-built RFLP panel.

    This page shows a summary of the recommended FH RFLP mutations, which are
    pre-calculated and stored in the system.
    """
    mutations = get_panel_summary() # Retrieve the summary data for the panel.
    return render_template("panel.html", mutations=mutations) # Pass data to the template for rendering.


@main.route("/analyze")
def analyze():
    """Renders the page for running a full RFLP analysis on a user-submitted mutation.

    This page provides an interface for users to input mutation details and trigger
    the bioinformatics pipeline.
    """
    return render_template("analyze.html")


# ── API Endpoints ─────────────────────────────────────────────

@main.route("/api/search")
def api_search():
    """
    API endpoint to search the RFLP panel by gene, mutation, or enzyme.

    Expects a GET request with a query parameter `q`.
    Example: `GET /api/search?q=LDLR`

    Returns:
        JSON: A JSON object containing search results and the count of results.
    """
    query = request.args.get("q", "").strip() # Get the search query from URL parameters.
    if not query:
        return jsonify({"error": "No search query provided."}), 400 # Return error if query is missing.
    
    results = search_panel(query) # Call the core function to perform the search.
    return jsonify({"results": results, "count": len(results)}) # Return results as JSON.


@main.route("/api/detail")
def api_detail():
    """
    API endpoint to retrieve full details for a specific mutation, including its simulated gel image.

    Expects a GET request with a query parameter `mutation`.
    Example: `GET /api/detail?mutation=c.408C>G`

    Returns:
        JSON: A JSON object containing detailed mutation information and the base64 encoded gel image.
    """
    mutation = request.args.get("mutation", "").strip() # Get the mutation identifier from URL parameters.
    if not mutation:
        return jsonify({"error": "No mutation provided."}), 400 # Return error if mutation is missing.
    
    result = get_mutation_detail(mutation) # Call the core function to get mutation details.
    return jsonify(result) # Return details as JSON.


@main.route("/api/analyze", methods=["POST"])
def api_analyze():
    """
    API endpoint to run the full RFLP analysis pipeline on a user-submitted mutation.

    Expects a POST request with a JSON body containing mutation details.
    Body: `{gene, cdna_change, chrom, pos, ref, alt}`

    Returns:
        JSON: A JSON object containing the results of the full analysis, including
              the best enzyme, fragment sizes, gel quality, and the base64 encoded gel image.
    """
    data = request.get_json() # Get JSON data from the request body.
    
    # Validate that all required fields are present in the request data.
    required = ["gene", "cdna_change", "chrom", "pos", "ref", "alt"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Missing field: {field}"}), 400 # Return error for missing fields.
    
    # Run the full bioinformatics pipeline with the provided mutation details.
    result = run_full_analysis(
        gene        = data["gene"],
        cdna_change = data["cdna_change"],
        chrom       = data["chrom"],
        pos         = data["pos"],
        ref         = data["ref"],
        alt         = data["alt"]
    )
    
    return jsonify(result) # Return the analysis results as JSON.


@main.route("/api/panel")
def api_panel():
    """
    API endpoint to return the full pre-built RFLP panel as JSON.

    Returns:
        JSON: A JSON object containing the complete panel data and the count of mutations.
    """
    mutations = get_panel_summary() # Retrieve the summary data for the panel.
    return jsonify({"panel": mutations, "count": len(mutations)}) # Return panel data as JSON.
