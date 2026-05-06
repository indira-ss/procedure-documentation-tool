from flask import Blueprint, request, jsonify
import re

from services.cache_service import generate_cache_key, get_cache, set_cache
from services.groq_client import call_groq

report_bp = Blueprint("report", __name__)

@report_bp.route("/generate-report", methods=["POST"])
def generate_report():

    data = request.get_json()

    if not data or "procedure_data" not in data:
        return jsonify({"error": "procedure_data required"}), 400

    raw = data["procedure_data"].strip()

    if not raw:
        return jsonify({"error": "empty input"}), 400

    # 🔐 CACHE KEY
    cache_key = generate_cache_key(raw)

    # 🔍 CHECK CACHE
    cached = get_cache(cache_key)
    if cached:
        return jsonify(cached), 200

    # 🤖 AI CALL
    response = call_groq(raw)

    if response is None:
        return jsonify({
            "title": "Report Unavailable",
            "summary": "AI service error",
            "is_fallback": True
        }), 200

    # 🧹 CLEAN RESPONSE
    clean = re.sub(r'```json|```', '', response).strip()

    try:
        parsed = {
            "title": "AI Report",
            "summary": clean,
            "input": raw
        }
    except:
        parsed = {"error": "parse failed"}

    # 💾 SAVE CACHE
    set_cache(cache_key, parsed)

    return jsonify(parsed)