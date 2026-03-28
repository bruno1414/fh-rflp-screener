#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""app/core/panel.py

This module manages the RFLP (Restriction Fragment Length Polymorphism) panel data
for Familial Hypercholesterolemia (FH) mutations. It provides functions to load,
search, and retrieve detailed information about RFLP candidates and the final
recommended panel, including generating simulated gel images.
"""

import pandas as pd  # Used for data manipulation and analysis with DataFrames.
import os            # Used for interacting with the operating system, e.g., path manipulation.
import ast           # Used for safely evaluating strings containing Python literal structures.
from app.core.pipeline import draw_gel_base64  # Imports a function to draw gel images as base64 strings.

# Define paths to the data files within the results directory.
# RESULTS_DIR is constructed relative to the current file to ensure portability.
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "results")
PANEL_CSV   = os.path.join(RESULTS_DIR, "final_panel.csv")         # Path to the CSV file containing the final recommended RFLP panel.
ALL_CSV     = os.path.join(RESULTS_DIR, "fh_rflp_candidates.csv")  # Path to the CSV file containing all RFLP candidates.


def load_panel():
    """Loads the final recommended 10-mutation RFLP panel from a CSV file.

    This panel is typically the result of a selection process from a larger set of candidates,
    often involving scoring and optimization (which might be AI-assisted in the broader pipeline).

    Returns:
        pd.DataFrame: A DataFrame containing the data for the final RFLP panel.
    """
    df = pd.read_csv(PANEL_CSV)
    return df


def load_all_candidates():
    """Loads all 23 RFLP candidates from a CSV file.

    These candidates represent potential mutations and their associated RFLP characteristics
    that were identified and analyzed in earlier stages of the pipeline.

    Returns:
        pd.DataFrame: A DataFrame containing data for all RFLP candidates.
    """
    df = pd.read_csv(ALL_CSV)
    return df


def search_panel(query: str) -> list:
    """
    Searches through all RFLP candidates based on a user-provided query.
    The search is performed across gene name, cDNA change, protein change, and best enzyme.

    Args:
        query (str): The search term provided by the user.

    Returns:
        list: A list of dictionaries, where each dictionary represents a matching RFLP candidate.
              Returns an empty list if no matches are found.
    """
    df = load_all_candidates()
    query = query.strip().upper()  # Normalize query for case-insensitive search.

    # Create a boolean mask for rows where any of the specified columns contain the query string.
    mask = (
        df["gene"].str.upper().str.contains(query, na=False) |         # Search in gene column.
        df["cdna_change"].str.upper().str.contains(query, na=False) |  # Search in cDNA change column.
        df["protein_change"].str.upper().str.contains(query, na=False) | # Search in protein change column.
        df["best_enzyme"].str.upper().str.contains(query, na=False)    # Search in best enzyme column.
    )

    matches = df[mask].copy()  # Filter the DataFrame based on the mask and create a copy.
    return matches.to_dict(orient="records") # Convert matching rows to a list of dictionaries.


def get_mutation_detail(cdna_change: str) -> dict:
    """
    Retrieves full details for a specific mutation, identified by its cDNA change,
    and generates a simulated gel image for visualization.

    Args:
        cdna_change (str): The cDNA change identifier for the mutation (e.g., "c.11470C>T").

    Returns:
        dict: A dictionary containing comprehensive details of the mutation, including
              gene, cDNA change, protein change, best enzyme, fragment sizes for wild-type
              and mutant alleles, RFLP score, and a base64 encoded simulated gel image.
              Returns an error dictionary if the mutation is not found or fragment data cannot be parsed.
    """
    df = load_all_candidates()

    row = df[df["cdna_change"] == cdna_change] # Find the row corresponding to the given cDNA change.
    if row.empty:
        return {"error": f"Mutation {cdna_change} not found in panel."}

    row = row.iloc[0] # Get the first (and likely only) matching row.

    try:
        # Safely evaluate string representations of lists of fragments into actual Python lists.
        # This is necessary because lists might be stored as strings in the CSV.
        wt_frags  = ast.literal_eval(str(row["wt_frags"]))
        mut_frags = ast.literal_eval(str(row["mut_frags"]))
    except:
        return {"error": "Could not parse fragment data."}

    # Generate a simulated gel image for the wild-type and mutant fragments.
    # The `draw_gel_base64` function (likely AI-generated or using bioinformatics libraries)
    # creates a visual representation of the RFLP pattern.
    gel_img = draw_gel_base64(
        wt_frags,
        mut_frags,
        title=f"{row["gene"]} {row["cdna_change"]} — {row["best_enzyme"]} digest"
    )

    # Return a structured dictionary of mutation details.
    return {
        "gene":           str(row["gene"]),
        "cdna_change":    str(row["cdna_change"]),
        "protein_change": str(row.get("protein_change", "")),
        "best_enzyme":    str(row["best_enzyme"]),
        "change_type":    str(row["change_type"]),
        "wt_frags":       [int(x) for x in wt_frags],   # Convert fragment sizes to integers.
        "mut_frags":      [int(x) for x in mut_frags],  # Convert fragment sizes to integers.
        "frag_diff_bp":   int(row["frag_diff_bp"]),
        "gel_quality":    str(row["gel_quality"]),
        "rflp_score":     float(row["rflp_score"]),
        "gel_image":      gel_img, # Base64 encoded image data.
    }


def get_panel_summary() -> list:
    """
    Retrieves a summary of the top 10 recommended RFLP panel mutations.

    Returns:
        list: A list of dictionaries, each representing a mutation in the panel
              with key summary details suitable for display.
    """
    df = load_panel()
    records = []
    for _, row in df.iterrows():
        records.append({
            "gene":           str(row["gene"]),
            "cdna_change":    str(row["cdna_change"]),
            "protein_change": str(row.get("protein_change", "")),
            "best_enzyme":    str(row["best_enzyme"]),
            "change_type":    str(row["change_type"]),
            "frag_diff_bp":   int(row["frag_diff_bp"]),
            "gel_quality":    str(row["gel_quality"]),
            "rflp_score":     float(row["rflp_score"]),
        })
    return records
