import pandas as pd
import os
import ast
from app.core.pipeline import draw_gel_base64

# Path to your results folder
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "results")
PANEL_CSV   = os.path.join(RESULTS_DIR, "final_panel.csv")
ALL_CSV     = os.path.join(RESULTS_DIR, "fh_rflp_candidates.csv")


def load_panel():
    """Load the final recommended 10-mutation panel."""
    df = pd.read_csv(PANEL_CSV)
    return df


def load_all_candidates():
    """Load all 23 RFLP candidates."""
    df = pd.read_csv(ALL_CSV)
    return df


def search_panel(query: str) -> list:
    """
    Search the panel by gene, mutation, or enzyme.
    Returns a list of matching rows as dictionaries.
    """
    df = load_all_candidates()
    query = query.strip().upper()

    mask = (
        df["gene"].str.upper().str.contains(query, na=False) |
        df["cdna_change"].str.upper().str.contains(query, na=False) |
        df["protein_change"].str.upper().str.contains(query, na=False) |
        df["best_enzyme"].str.upper().str.contains(query, na=False)
    )

    matches = df[mask].copy()
    return matches.to_dict(orient="records")


def get_mutation_detail(cdna_change: str) -> dict:
    """
    Get full details for a specific mutation including gel image.
    """
    df = load_all_candidates()

    row = df[df["cdna_change"] == cdna_change]
    if row.empty:
        return {"error": f"Mutation {cdna_change} not found in panel."}

    row = row.iloc[0]

    try:
        wt_frags  = ast.literal_eval(str(row["wt_frags"]))
        mut_frags = ast.literal_eval(str(row["mut_frags"]))
    except:
        return {"error": "Could not parse fragment data."}

    gel_img = draw_gel_base64(
        wt_frags,
        mut_frags,
        title=f"{row['gene']} {row['cdna_change']} — {row['best_enzyme']} digest"
    )

    return {
        "gene":           str(row["gene"]),
        "cdna_change":    str(row["cdna_change"]),
        "protein_change": str(row.get("protein_change", "")),
        "best_enzyme":    str(row["best_enzyme"]),
        "change_type":    str(row["change_type"]),
        "wt_frags":       [int(x) for x in wt_frags],
        "mut_frags":      [int(x) for x in mut_frags],
        "frag_diff_bp":   int(row["frag_diff_bp"]),
        "gel_quality":    str(row["gel_quality"]),
        "rflp_score":     float(row["rflp_score"]),
        "gel_image":      gel_img,
    }


def get_panel_summary() -> list:
    """
    Return the full top 10 panel as a list of dicts for display.
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