from flask import Blueprint, render_template, request, jsonify
from app.core.panel import (
    get_panel_summary,
    search_panel,
    get_mutation_detail
)
from app.core.pipeline import run_full_analysis

main = Blueprint("main", __name__)


# ── Pages ─────────────────────────────────────────────────────

@main.route("/")
def index():
    """Home page."""
    return render_template("index.html")


@main.route("/panel")
def panel():
    """Pre-built panel lookup page."""
    mutations = get_panel_summary()
    return render_template("panel.html", mutations=mutations)


@main.route("/analyze")
def analyze():
    """Full pipeline analysis page."""
    return render_template("analyze.html")


# ── API Endpoints ─────────────────────────────────────────────

@main.route("/api/search")
def api_search():
    """
    Search the panel by gene, mutation, or enzyme.
    GET /api/search?q=LDLR
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "No search query provided."})
    
    results = search_panel(query)
    return jsonify({"results": results, "count": len(results)})


@main.route("/api/detail")
def api_detail():
    """
    Get full details for a mutation including gel image.
    GET /api/detail?mutation=c.408C>G
    """
    mutation = request.args.get("mutation", "").strip()
    if not mutation:
        return jsonify({"error": "No mutation provided."})
    
    result = get_mutation_detail(mutation)
    return jsonify(result)


@main.route("/api/analyze", methods=["POST"])
def api_analyze():
    """
    Run full pipeline on a user-submitted mutation.
    POST /api/analyze
    Body: {gene, cdna_change, chrom, pos, ref, alt}
    """
    data = request.get_json()
    
    # Validate required fields
    required = ["gene", "cdna_change", "chrom", "pos", "ref", "alt"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Missing field: {field}"})
    
    result = run_full_analysis(
        gene        = data["gene"],
        cdna_change = data["cdna_change"],
        chrom       = data["chrom"],
        pos         = data["pos"],
        ref         = data["ref"],
        alt         = data["alt"]
    )
    
    return jsonify(result)


@main.route("/api/panel")
def api_panel():
    """Return the full panel as JSON."""
    mutations = get_panel_summary()
    return jsonify({"panel": mutations, "count": len(mutations)})