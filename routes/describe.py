import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, request, jsonify
from services.groq_client import call_groq
from services.sanitiser import sanitise_input, InputValidationError

logger = logging.getLogger(__name__)
describe_bp = Blueprint("describe", __name__)
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "describe_prompt.txt"

FALLBACK_RESPONSE = {
    "summary": "Description could not be generated at this time.",
    "purpose": "The AI service is temporarily unavailable.",
    "steps": [],
    "prerequisites": [],
    "expected_outcome": "N/A",
    "estimated_duration": "N/A",
    "difficulty_level": "N/A",
    "is_fallback": True,
}

@describe_bp.route("/describe", methods=["POST"])
def describe():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "request body must be JSON"}), 400

    try:
        title = sanitise_input(data.get("title", ""), field_name="title")
        category = sanitise_input(data.get("category", ""), field_name="category")
        raw_steps = sanitise_input(data.get("raw_steps", ""), field_name="raw_steps")
    except InputValidationError as e:
        return jsonify({"error": str(e)}), 400

    generated_at = datetime.now(timezone.utc).isoformat()

    try:
        template = PROMPT_PATH.read_text(encoding="utf-8")
        prompt = template.replace("{title}", title).replace("{category}", category).replace("{raw_steps}", raw_steps)
    except Exception as e:
        logger.error("Prompt load error: %s", e)
        return jsonify({**FALLBACK_RESPONSE, "generated_at": generated_at}), 200

    raw_response = call_groq(prompt, temperature=0.3, max_tokens=1024)

    if raw_response is None:
        return jsonify({**FALLBACK_RESPONSE, "generated_at": generated_at}), 200

    try:
        clean = raw_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(clean)
        result["generated_at"] = generated_at
        result.setdefault("is_fallback", False)
        return jsonify(result), 200
    except (json.JSONDecodeError, ValueError):
        return jsonify({**FALLBACK_RESPONSE, "generated_at": generated_at}), 200