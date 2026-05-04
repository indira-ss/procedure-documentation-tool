"""
routes/recommend.py
POST /recommend
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, request, jsonify
from services.groq_client import call_groq
from services.sanitiser import sanitise_input, InputValidationError

logger = logging.getLogger(__name__)
recommend_bp = Blueprint("recommend", __name__)
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "recommend_prompt.txt"

FALLBACK_RECOMMENDATIONS = [
    {
        "action_type": "DOCUMENT",
        "description": "AI recommendations are temporarily unavailable.",
        "priority": "MEDIUM",
        "estimated_impact": "Ensures procedure quality is maintained.",
    }
]

@recommend_bp.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "request body must be JSON"}), 400

    try:
        title = sanitise_input(data.get("title", ""), field_name="title")
        description = sanitise_input(data.get("description", ""), field_name="description")
        steps = sanitise_input(data.get("steps", ""), field_name="steps")
    except InputValidationError as e:
        return jsonify({"error": str(e)}), 400

    template = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = template.replace("{title}", title).replace("{description}", description).replace("{steps}", steps)

    raw_response = call_groq(prompt, temperature=0.3, max_tokens=1024)
    generated_at = datetime.now(timezone.utc).isoformat()

    if raw_response is None:
        return jsonify({
            "recommendations": FALLBACK_RECOMMENDATIONS,
            "generated_at": generated_at,
            "is_fallback": True,
        }), 200

    try:
        clean = raw_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(clean)
        recommendations = result.get("recommendations", [])
    except (json.JSONDecodeError, ValueError):
        return jsonify({
            "recommendations": FALLBACK_RECOMMENDATIONS,
            "generated_at": generated_at,
            "is_fallback": True,
        }), 200

    return jsonify({
        "recommendations": recommendations,
        "generated_at": generated_at,
        "is_fallback": False,
    }), 200