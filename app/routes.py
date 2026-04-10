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
        return jsonify({"error": "No search query provided."}), 400

    try:
        results = search_panel(query)
        return jsonify({"results": results, "count": len(results)})
    except Exception:
        return jsonify({"error": "Failed to search panel."}), 500


@main.route("/api/detail")
def api_detail():
    """
    Get full details for a mutation including gel image.
    GET /api/detail?mutation=c.408C>G
    """
    mutation = request.args.get("mutation", "").strip()
    if not mutation:
        return jsonify({"error": "No mutation provided."}), 400

    try:
        result = get_mutation_detail(mutation)
        if result.get("error"):
            return jsonify(result), 404
        return jsonify(result)
    except Exception:
        return jsonify({"error": "Failed to fetch mutation details."}), 500


@main.route("/api/analyze", methods=["POST"])
def api_analyze():
    """
    Run full pipeline on a user-submitted mutation.
    POST /api/analyze
    Body: {gene, cdna_change, chrom, pos, ref, alt}
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body."}), 400

    # Validate required fields
    required = ["gene", "cdna_change", "chrom", "pos", "ref", "alt"]
    for field in required:
        value = data.get(field)
        if value is None or str(value).strip() == "":
            return jsonify({"error": f"Missing field: {field}"}), 400

    try:
        result = run_full_analysis(
            gene=data["gene"].strip(),
            cdna_change=data["cdna_change"].strip(),
            chrom=str(data["chrom"]).strip(),
            pos=str(data["pos"]).strip(),
            ref=str(data["ref"]).strip().upper(),
            alt=str(data["alt"]).strip().upper()
        )
        if isinstance(result, dict) and result.get("error"):
            return jsonify(result), 400
        return jsonify(result)
    except Exception:
        return jsonify({"error": "Analysis failed due to an internal error."}), 500


@main.route("/api/panel")
def api_panel():
    """Return the full panel as JSON."""
    try:
        mutations = get_panel_summary()
        return jsonify({"panel": mutations, "count": len(mutations)})
    except Exception:
        return jsonify({"error": "Failed to load panel data."}), 500
