import requests
import time
import io
import base64
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # No display needed — runs on server
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from Bio.Restriction import RestrictionBatch, Analysis, CommOnly
from Bio.Seq import Seq, MutableSeq

# ── Sequence Retrieval ────────────────────────────────────────

def get_sequence(chrom, pos, window=300):
    """Fetch reference sequence from Ensembl around a position."""
    start = int(pos) - window
    end   = int(pos) + window
    url   = f"https://rest.ensembl.org/sequence/region/human/{chrom}:{start}..{end}"
    resp  = requests.get(url, headers={"Content-Type": "text/plain"})
    if resp.status_code == 200:
        return resp.text.strip(), window
    return None, None


def introduce_mutation(wt_seq, position, ref, alt):
    """Introduce a point mutation at a position in the sequence."""
    seq = list(wt_seq)
    complements = {"A":"T","T":"A","G":"C","C":"G"}
    actual = seq[position].upper()
    if ref and actual != ref.upper():
        comp = complements.get(ref.upper(), "?")
        if actual == comp:
            alt = complements.get(alt.upper(), alt)
    if alt:
        seq[position] = alt.upper()
    return "".join(seq)


# ── Restriction Analysis ──────────────────────────────────────

def cuts_to_fragments(sequence, cut_positions):
    """Convert cut positions to fragment sizes in bp."""
    if not cut_positions:
        return [len(sequence)]
    boundaries = [0] + sorted(cut_positions) + [len(sequence)]
    return [boundaries[i+1] - boundaries[i]
            for i in range(len(boundaries)-1)]


def find_informative_enzymes(wt_seq, mut_seq):
    """Scan all commercial enzymes and return informative ones."""
    rb  = RestrictionBatch(CommOnly)
    wt  = Seq(wt_seq)
    mut = Seq(mut_seq)

    wt_results  = Analysis(rb, wt,  linear=True).full()
    mut_results = Analysis(rb, mut, linear=True).full()

    informative = []
    for enzyme in rb:
        wt_cuts  = list(wt_results[enzyme])
        mut_cuts = list(mut_results[enzyme])
        if wt_cuts == mut_cuts:
            continue

        if len(wt_cuts) > len(mut_cuts):
            change_type = "site_destroyed"
        elif len(wt_cuts) < len(mut_cuts):
            change_type = "site_created"
        else:
            change_type = "position_shifted"

        wt_frags  = cuts_to_fragments(wt_seq,  wt_cuts)
        mut_frags = cuts_to_fragments(mut_seq, mut_cuts)
        frag_diff = abs(max(wt_frags) - max(mut_frags))

        informative.append({
            "enzyme":       str(enzyme),
            "change_type":  change_type,
            "wt_frags":     wt_frags,
            "mut_frags":    mut_frags,
            "frag_diff_bp": frag_diff,
        })

    informative.sort(key=lambda x: x["frag_diff_bp"], reverse=True)
    return informative


def assign_quality(frag_diff):
    """Assign gel quality tier based on fragment size difference."""
    if frag_diff >= 150:  return "excellent"
    elif frag_diff >= 50: return "good"
    elif frag_diff > 0:   return "poor"
    else:                 return "unusable"


# ── Gel Visualization ─────────────────────────────────────────

def draw_gel_base64(wt_frags, mut_frags, title,
                    ladder=[100,200,300,400,500,600,800,1000]):
    """
    Generate a gel simulation and return it as a base64 PNG string.
    This lets Flask send the image directly to the browser.
    """
    het_frags = sorted(list(set(wt_frags + mut_frags)), reverse=True)

    samples = [
        {"label": "WT",     "fragments": wt_frags,  "color": "#22d3ee"},
        {"label": "Het",    "fragments": het_frags,  "color": "#facc15"},
        {"label": "Mutant", "fragments": mut_frags,  "color": "#f87171"},
    ]

    n_lanes = len(samples) + 1
    fig, ax = plt.subplots(figsize=(2 + n_lanes * 1.4, 7))
    ax.set_facecolor("#111827")
    fig.patch.set_facecolor("#111827")

    def bp_to_y(bp):
        log_bp  = np.log10(np.clip(bp, 80, 1200))
        log_min = np.log10(80)
        log_max = np.log10(1200)
        return 0.92 - (log_bp - log_min) / (log_max - log_min) * 0.84

    lane_w  = 0.55
    spacing = 1.0
    all_lanes = (
        [{"label":"Ladder","fragments":ladder,
          "color":"#9ca3af","is_ladder":True}] +
        [dict(s, is_ladder=False) for s in samples]
    )

    for i, lane in enumerate(all_lanes):
        x     = i * spacing
        color = lane.get("color", "#22d3ee")
        for bp in lane["fragments"]:
            y     = bp_to_y(bp)
            alpha = 0.45 + 0.55 * min(bp / 600, 1.0)
            rect  = mpatches.FancyBboxPatch(
                (x - lane_w/2, y - 0.013/2),
                lane_w, 0.013,
                boxstyle="round,pad=0.003",
                facecolor=color, edgecolor="none", alpha=alpha
            )
            ax.add_patch(rect)
            if lane["is_ladder"] or len(lane["fragments"]) <= 4:
                ax.text(x + lane_w/2 + 0.08, y,
                        f"{bp} bp", va="center", ha="left",
                        fontsize=6.5, color="#d1d5db",
                        fontfamily="monospace")

    for i, lane in enumerate(all_lanes):
        ax.text(i * spacing, -0.04, lane["label"],
                ha="center", va="top", fontsize=9,
                color="white", fontweight="bold")
        well = mpatches.FancyBboxPatch(
            (i * spacing - lane_w/2, 0.935),
            lane_w, 0.03,
            boxstyle="round,pad=0.002",
            facecolor="#374151", edgecolor="#6b7280", linewidth=0.5
        )
        ax.add_patch(well)

    ax.set_title(title, color="white", fontsize=10,
                 fontweight="bold", pad=10)
    ax.set_xlim(-0.7, (len(all_lanes)-1) * spacing + 0.9)
    ax.set_ylim(-0.08, 1.0)
    ax.axis("off")
    plt.tight_layout()

    # Convert to base64 string instead of saving to disk
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150,
                bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    return img_base64


# ── Full Pipeline ─────────────────────────────────────────────

def run_full_analysis(gene, cdna_change, chrom, pos, ref, alt):
    """
    Run the complete pipeline for a single mutation.
    Returns a results dictionary the app can display.
    """
    # 1. Fetch sequences
    wt_seq, var_pos = get_sequence(chrom, pos, window=300)
    if not wt_seq:
        return {"error": "Could not retrieve sequence from Ensembl."}

    # 2. Introduce mutation
    mut_seq = introduce_mutation(wt_seq, var_pos, ref, alt)

    # 3. Scan enzymes
    enzymes = find_informative_enzymes(wt_seq, mut_seq)
    if not enzymes:
        return {"error": "No informative restriction enzymes found."}

    # 4. Take best enzyme
    best = enzymes[0]
    quality = assign_quality(best["frag_diff_bp"])

    # 5. Generate gel image
    gel_img = draw_gel_base64(
        best["wt_frags"],
        best["mut_frags"],
        title=f"{gene} {cdna_change} — {best['enzyme']} digest"
    )

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
        "all_enzymes":  enzymes[:5],  # Top 5 alternatives
        "n_enzymes":    len(enzymes),
    }