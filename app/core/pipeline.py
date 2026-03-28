#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""app/core/pipeline.py

This module implements the core bioinformatics pipeline for the FH RFLP Screener.
It includes functionalities for retrieving DNA sequences, introducing mutations,
performing restriction enzyme analysis, and simulating gel electrophoresis results.
Many of these steps involve computational biology techniques that can be considered
AI-assisted in their underlying algorithms (e.g., sequence alignment, pattern matching).
"""

import requests       # Used for making HTTP requests to external APIs (e.g., Ensembl).
import time           # Used for time-related functions, though not extensively in this version.
import io             # Used for in-memory binary streams for image processing.
import base64         # Used for encoding binary image data into base64 strings for web display.
import pandas as pd   # Used for data manipulation, though less directly in this specific module.
import matplotlib     # Core plotting library.
matplotlib.use("Agg") # Set Matplotlib backend to 'Agg' for non-interactive plotting, suitable for server environments.
import matplotlib.pyplot as plt       # Used for creating plots and figures.
import matplotlib.patches as mpatches # Used for creating custom shapes/patches in plots.
import numpy as np                    # Used for numerical operations, especially for log-scale calculations.
from Bio.Restriction import RestrictionBatch, Analysis, CommOnly # Biopython modules for restriction enzyme analysis.
from Bio.Seq import Seq, MutableSeq                              # Biopython modules for sequence handling.

# ── Sequence Retrieval ────────────────────────────────────────

def get_sequence(chrom: str, pos: int, window: int = 300) -> tuple[str | None, int | None]:
    """Fetches a reference DNA sequence from the Ensembl REST API around a specified genomic position.

    This function queries the Ensembl human genome database to retrieve a DNA sequence
    flanking a given coordinate. This is a crucial first step for any in-silico RFLP analysis,
    as it provides the wild-type sequence against which mutations will be introduced.

    Args:
        chrom (str): The chromosome number (e.g., "1", "X").
        pos (int): The 1-based genomic position of interest.
        window (int): The number of base pairs to retrieve on either side of the position.
                      The total sequence length will be `2 * window + 1`.

    Returns:
        tuple[str | None, int | None]: A tuple containing:
            - The fetched wild-type DNA sequence as a string (or None if retrieval fails).
            - The 0-based relative position of the original `pos` within the fetched sequence (or None).
    """
    start = int(pos) - window
    end   = int(pos) + window
    # Construct the Ensembl REST API URL for sequence retrieval.
    url   = f"https://rest.ensembl.org/sequence/region/human/{chrom}:{start}..{end}"
    # Make an HTTP GET request to the Ensembl API.
    resp  = requests.get(url, headers={"Content-Type": "text/plain"})
    if resp.status_code == 200:
        # Return the sequence and the relative position of the original 'pos' within the window.
        return resp.text.strip(), window
    return None, None


def introduce_mutation(wt_seq: str, position: int, ref: str, alt: str) -> str:
    """Introduces a single nucleotide polymorphism (SNP) or point mutation into a wild-type DNA sequence.

    This function simulates the presence of a mutation by replacing a base at a specific position.
    It handles potential strand differences by complementing the `alt` allele if the `ref` allele
    is on the opposite strand (based on the provided `ref` and the actual base in `wt_seq`).

    Args:
        wt_seq (str): The wild-type DNA sequence.
        position (int): The 0-based index in `wt_seq` where the mutation occurs.
        ref (str): The reference allele at the given position.
        alt (str): The alternative (mutant) allele to introduce.

    Returns:
        str: The mutated DNA sequence.
    """
    seq = list(wt_seq) # Convert sequence to a mutable list of characters.
    complements = {"A":"T","T":"A","G":"C","C":"G"} # Dictionary for base complementarity.
    actual = seq[position].upper() # Get the actual base at the position in the wild-type sequence.

    # Check if the provided 'ref' allele matches the actual base, considering potential reverse complement.
    if ref and actual != ref.upper():
        comp = complements.get(ref.upper(), "?")
        if actual == comp:
            # If 'ref' is on the opposite strand, complement the 'alt' allele as well.
            alt = complements.get(alt.upper(), alt)

    if alt:
        seq[position] = alt.upper() # Introduce the alternative allele.
    return "".join(seq) # Join the list back into a string.


# ── Restriction Analysis ──────────────────────────────────────

def cuts_to_fragments(sequence: str, cut_positions: list[int]) -> list[int]:
    """Converts a list of restriction enzyme cut positions into a list of DNA fragment sizes.

    This function simulates the outcome of a restriction digest, where a DNA sequence
    is cut at specific points, resulting in fragments of varying lengths. This is a core
    calculation for RFLP analysis.

    Args:
        sequence (str): The DNA sequence that was digested.
        cut_positions (list[int]): A sorted list of 0-based indices where the enzyme cuts the sequence.

    Returns:
        list[int]: A list of integers representing the sizes (in base pairs) of the resulting DNA fragments.
                   If no cuts occur, the original sequence length is returned as a single fragment.
    """
    if not cut_positions:
        return [len(sequence)] # If no cuts, the entire sequence is one fragment.
    # Define boundaries including the start (0), all cut positions, and the end (sequence length).
    boundaries = [0] + sorted(cut_positions) + [len(sequence)]
    # Calculate fragment sizes by taking the difference between consecutive boundaries.
    return [boundaries[i+1] - boundaries[i]
            for i in range(len(boundaries)-1)]


def find_informative_enzymes(wt_seq: str, mut_seq: str) -> list[dict]:
    """Scans a comprehensive list of commercial restriction enzymes to identify those
    that produce a different digestion pattern between a wild-type and a mutated sequence.

    This function leverages Biopython's Restriction module to perform in-silico restriction digests.
    It's a key AI-assisted component as it automates the laborious process of checking hundreds
    of enzymes, identifying those that are informative ones.

    Args:
        wt_seq (str): The wild-type DNA sequence.
        mut_seq (str): The mutated DNA sequence.

    Returns:
        list[dict]: A list of dictionaries, each describing an informative enzyme
                    and its digestion characteristics (change type, fragment sizes,
                    and fragment difference).
    """
    rb  = RestrictionBatch(CommOnly) # Initialize with a batch of commonly available restriction enzymes.
    wt  = Seq(wt_seq)                # Convert wild-type string to Biopython Seq object.
    mut = Seq(mut_seq)               # Convert mutant string to Biopython Seq object.

    # Perform in-silico restriction analysis for both wild-type and mutant sequences.
    # `linear=True` indicates that the DNA is linear, not circular.
    wt_results  = Analysis(rb, wt,  linear=True).full()
    mut_results = Analysis(rb, mut, linear=True).full()

    informative = []
    for enzyme in rb:
        wt_cuts  = list(wt_results[enzyme])  # Get cut positions for wild-type sequence.
        mut_cuts = list(mut_results[enzyme]) # Get cut positions for mutant sequence.

        # If the cut patterns are identical, the enzyme is not informative for this mutation.
        if wt_cuts == mut_cuts:
            continue

        # Determine the type of change caused by the mutation (site created, destroyed, or shifted).
        if len(wt_cuts) > len(mut_cuts):
            change_type = "site_destroyed"
        elif len(wt_cuts) < len(mut_cuts):
            change_type = "site_created"
        else:
            change_type = "position_shifted" # e.g., a cut site moves but the number of cuts remains the same.

        # Convert cut positions to fragment sizes for both sequences.
        wt_frags  = cuts_to_fragments(wt_seq,  wt_cuts)
        mut_frags = cuts_to_fragments(mut_seq, mut_cuts)
        # Calculate the absolute difference between the largest fragments, a key metric for gel resolution.
        frag_diff = abs(max(wt_frags) - max(mut_frags))

        informative.append({
            "enzyme":       str(enzyme),       # Name of the restriction enzyme.
            "change_type":  change_type,       # Type of change (site_destroyed, site_created, position_shifted).
            "wt_frags":     wt_frags,
            "mut_frags":    mut_frags,
            "frag_diff_bp": frag_diff,         # Difference in base pairs of the largest fragments.
        })

    # Sort informative enzymes by the fragment difference in descending order.
    # This prioritizes enzymes that create more easily distinguishable patterns on a gel.
    informative.sort(key=lambda x: x["frag_diff_bp"], reverse=True)
    return informative


def assign_quality(frag_diff: int) -> str:
    """Assigns a qualitative score to the RFLP gel based on the fragment size difference.

    This function helps in quickly assessing the visual distinguishability of the RFLP pattern
    on a gel, which is important for practical diagnostic applications.

    Args:
        frag_diff (int): The absolute difference in base pairs between the largest wild-type
                         and mutant fragments.

    Returns:
        str: A qualitative assessment of the gel (e.g., "excellent", "good", "poor", "unusable").
    """
    if frag_diff >= 150:  return "excellent"
    elif frag_diff >= 50: return "good"
    elif frag_diff > 0:   return "poor"
    else:                 return "unusable"


# ── Gel Visualization ─────────────────────────────────────────

def draw_gel_base64(wt_frags: list[int], mut_frags: list[int], title: str,
                    ladder: list[int] = [100,200,300,400,500,600,800,1000]) -> str:
    """
    Generates a simulated gel electrophoresis image for RFLP analysis and returns it as a base64 encoded PNG string.

    This function uses Matplotlib to create a visual representation of how DNA fragments
    would separate on an agarose gel. It includes lanes for wild-type, mutant, and heterozygous
    patterns, along with a DNA ladder for size reference. This visualization is crucial for
    interpreting RFLP results and is often an AI-generated component in bioinformatics tools.

    Args:
        wt_frags (list[int]): List of fragment sizes (bp) for the wild-type allele.
        mut_frags (list[int]): List of fragment sizes (bp) for the mutant allele.
        title (str): The title to display above the gel image.
        ladder (list[int]): List of fragment sizes (bp) for the DNA ladder.

    Returns:
        str: A base64 encoded string of the generated PNG gel image.
    """
    # Calculate heterozygous fragments: a combination of unique wild-type and mutant fragments.
    het_frags = sorted(list(set(wt_frags + mut_frags)), reverse=True)

    # Define the samples to be displayed on the gel.
    samples = [
        {"label": "WT",     "fragments": wt_frags,  "color": "#22d3ee"}, # Wild-type lane.
        {"label": "Het",    "fragments": het_frags, "color": "#facc15"}, # Heterozygous lane.
        {"label": "Mutant", "fragments": mut_frags, "color": "#f87171"}, # Mutant lane.
    ]

    n_lanes = len(samples) + 1 # Total number of lanes, including the ladder.
    fig, ax = plt.subplots(figsize=(2 + n_lanes * 1.4, 7)) # Create figure and axes for the plot.
    ax.set_facecolor("#111827") # Set background color for the gel area.
    fig.patch.set_facecolor("#111827") # Set background color for the entire figure.

    def bp_to_y(bp: int) -> float:
        """Converts base pair size to a y-coordinate for plotting on a log-scale gel.

        This simulates the non-linear migration of DNA fragments in an agarose gel,
        where smaller fragments travel further (lower y-coordinate) and larger fragments
        travel less (higher y-coordinate), typically on a logarithmic scale.
        """
        log_bp  = np.log10(np.clip(bp, 80, 1200)) # Log-transform bp, clipping to a reasonable range.
        log_min = np.log10(80)
        log_max = np.log10(1200)
        # Normalize to a y-coordinate range (0.92 to 0.08) for visual representation.
        return 0.92 - (log_bp - log_min) / (log_max - log_min) * 0.84

    lane_w  = 0.55  # Width of each lane.
    spacing = 1.0   # Spacing between lanes.
    # Combine ladder and samples for iteration.
    all_lanes = (
        [{"label":"Ladder","fragments":ladder,
          "color":"#9ca3af","is_ladder":True}] +
        [dict(s, is_ladder=False) for s in samples]
    )

    # Plot each fragment as a rectangular band on the gel.
    for i, lane in enumerate(all_lanes):
        x     = i * spacing # X-coordinate for the center of the lane.
        color = lane.get("color", "#22d3ee") # Color of the fragment bands.
        for bp in lane["fragments"]:
            y     = bp_to_y(bp) # Convert bp to y-coordinate.
            # Adjust alpha (transparency) based on fragment size for visual effect.
            alpha = 0.45 + 0.55 * min(bp / 600, 1.0)
            rect  = mpatches.FancyBboxPatch(
                (x - lane_w/2, y - 0.013/2), # Position of the fragment band.
                lane_w, 0.013,               # Width and height of the band.
                boxstyle="round,pad=0.003",  # Rounded corners for the band.
                facecolor=color, edgecolor="none", alpha=alpha
            )
            ax.add_patch(rect) # Add the fragment band to the plot.
            # Add text labels for fragment sizes, especially for ladder and small number of fragments.
            if lane["is_ladder"] or len(lane["fragments"]) <= 4:
                ax.text(x + lane_w/2 + 0.08, y,
                        f"{bp} bp", va="center", ha="left",
                        fontsize=6.5, color="#d1d5db",
                        fontfamily="monospace")

    # Add lane labels (WT, Het, Mutant, Ladder) and well representations.
    for i, lane in enumerate(all_lanes):
        ax.text(i * spacing, -0.04, lane["label"],
                ha="center", va="top", fontsize=9,
                color="white", fontweight="bold")
        well = mpatches.FancyBboxPatch(
            (i * spacing - lane_w/2, 0.935), # Position of the well.
            lane_w, 0.03,
            boxstyle="round,pad=0.002",
            facecolor="#374151", edgecolor="#6b7280", linewidth=0.5
        )
        ax.add_patch(well)

    ax.set_title(title, color="white", fontsize=10,
                 fontweight="bold", pad=10) # Set the title of the gel.
    ax.set_xlim(-0.7, (len(all_lanes)-1) * spacing + 0.9) # Set x-axis limits.
    ax.set_ylim(-0.08, 1.0) # Set y-axis limits.
    ax.axis("off") # Hide axes.
    plt.tight_layout() # Adjust layout to prevent labels from overlapping.

    # Convert the Matplotlib figure to a base64 encoded PNG string.
    buf = io.BytesIO() # Create an in-memory binary stream.
    plt.savefig(buf, format="png", dpi=150,
                bbox_inches="tight",
                facecolor=fig.get_facecolor()) # Save figure to the buffer.
    plt.close() # Close the plot to free up memory.
    buf.seek(0) # Reset buffer position to the beginning.
    img_base64 = base64.b64encode(buf.read()).decode("utf-8") # Encode to base64.
    return img_base64


# ── Full Pipeline ─────────────────────────────────────────────

def run_full_analysis(gene: str, cdna_change: str, chrom: str, pos: int, ref: str, alt: str) -> dict:
    """
    Executes the complete RFLP analysis pipeline for a given mutation.

    This function orchestrates the entire process: fetching sequences, introducing the mutation,
    identifying informative restriction enzymes, assigning a quality score, and generating a
    simulated gel image. It acts as the main entry point for analyzing a single mutation
    through the RFLP screening workflow.

    Args:
        gene (str): The gene symbol (e.g., "LDLR").
        cdna_change (str): The cDNA change of the mutation (e.g., "c.11470C>T").
        chrom (str): The chromosome number.
        pos (int): The genomic position of the mutation.
        ref (str): The reference allele.
        alt (str): The alternative (mutant) allele.

    Returns:
        dict: A dictionary containing the results of the analysis, including the best enzyme,
              fragment sizes, gel quality, and the base64 encoded gel image. Returns an error
              dictionary if any step of the pipeline fails.
    """
    # 1. Fetch sequences from Ensembl.
    wt_seq, var_pos = get_sequence(chrom, pos, window=300)
    if not wt_seq:
        return {"error": "Could not retrieve sequence from Ensembl."}

    # 2. Introduce the mutation into the wild-type sequence.
    mut_seq = introduce_mutation(wt_seq, var_pos, ref, alt)

    # 3. Scan for informative restriction enzymes.
    enzymes = find_informative_enzymes(wt_seq, mut_seq)
    if not enzymes:
        return {"error": "No informative restriction enzymes found."}

    # 4. Select the best enzyme (the one with the largest fragment difference) and assign quality.
    best = enzymes[0]
    quality = assign_quality(best["frag_diff_bp"])

    # 5. Generate the simulated gel image for the best enzyme.
    gel_img = draw_gel_base64(
        best["wt_frags"],
        best["mut_frags"],
        title=f"{gene} {cdna_change} — {best["enzyme"]} digest"
    )

    # Return a comprehensive dictionary of the analysis results.
    return {
        "gene":         gene,
        "cdna_change":  cdna_change,
        "best_enzyme":  best["enzyme"],
        "change_type":  best["change_type"],
        "wt_frags":     best["wt_frags"],
        "mut_frags":    best["mut_frags"],
        "frag_diff_bp": best["frag_diff_bp"],
        "gel_quality":  quality,
        "gel_image":    gel_img,
        "all_enzymes":  enzymes[:5],  # Include top 5 alternative enzymes for consideration.
        "n_enzymes":    len(enzymes),
    }
