
from datetime import datetime, timezone
import json
import logging

from flask import Blueprint, request, jsonify

from services.groq_client import call_groq, load_prompt, cache_key

logger = logging.getLogger(__name__)

report_bp = Blueprint("report", __name__)

# --------------------------------------------------------------------------- #
# Fallback template — returned when Groq is unavailable                      #
# --------------------------------------------------------------------------- #

FALLBACK_REPORT = {
    "title": "Report Temporarily Unavailable",
    "summary": "The AI report generation service is currently unavailable. Please try again shortly.",
    "overview": {
        "purpose": "N/A",
        "scope": "N/A",
        "prerequisites": [],
        "estimated_duration": "N/A",
    },
    "key_items": [],
    "recommendations": [],
    "compliance_notes": "Unable to assess compliance at this time.",
    "quality_score": 0,
    "is_fallback": True,
}


# --------------------------------------------------------------------------- #
# Input validation                                                             #
# --------------------------------------------------------------------------- #

REQUIRED_FIELDS = ["title", "description"]


def _validate(data: dict) -> str | None:
    """Return an error message string, or None if valid."""
    if not data:
        return "Request body must be JSON."
    for field in REQUIRED_FIELDS:
        if not data.get(field, "").strip():
            return f"Field '{field}' is required and must not be blank."
    if len(data.get("title", "")) > 300:
        return "Field 'title' must not exceed 300 characters."
    if len(data.get("description", "")) > 5000:
        return "Field 'description' must not exceed 5000 characters."
    return None


# --------------------------------------------------------------------------- #
# Redis cache helper (optional — skips gracefully if Redis unavailable)       #
# --------------------------------------------------------------------------- #

def _get_redis():
    try:
        from flask import current_app
        return current_app.extensions.get("redis")
    except Exception:
        return None


CACHE_TTL = 900  # 15 minutes


def _cache_get(key: str):
    r = _get_redis()
    if not r:
        return None
    try:
        value = r.get(key)
        return json.loads(value) if value else None
    except Exception:
        return None


def _cache_set(key: str, value: dict):
    r = _get_redis()
    if not r:
        return
    try:
        r.setex(key, CACHE_TTL, json.dumps(value))
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# Endpoint                                                                     #
# --------------------------------------------------------------------------- #

@report_bp.route("/generate-report", methods=["POST"])
def generate_report():
    """
    Generate a structured procedure documentation report using AI.

    Request JSON:
    {
        "title":            "string (required)",
        "description":      "string (required)",
        "category":         "string (optional)",
        "status":           "string (optional)",
        "created_by":       "string (optional)",
        "steps":            "string (optional)",
        "additional_context": "string (optional)"
    }

    Response JSON:
    {
        "title": "...",
        "summary": "...",
        "overview": { "purpose", "scope", "prerequisites", "estimated_duration" },
        "key_items": [ { "item", "description", "importance", "notes" } ],
        "recommendations": [ { "action_type", "description", "priority", "rationale" } ],
        "compliance_notes": "...",
        "quality_score": 0-10,
        "generated_at": "ISO-8601",
        "is_fallback": false
    }
    """
    data = request.get_json(silent=True)

    # ── Validate ─────────────────────────────────────────────────────────── #
    error = _validate(data)
    if error:
        return jsonify({"error": error}), 400

    # ── Normalise inputs ──────────────────────────────────────────────────── #
    payload = {
        "title":              data["title"].strip(),
        "description":        data["description"].strip(),
        "category":           data.get("category", "General").strip(),
        "status":             data.get("status", "Draft").strip(),
        "created_by":         data.get("created_by", "Unknown").strip(),
        "steps":              data.get("steps", "Not provided").strip(),
        "additional_context": data.get("additional_context", "None").strip(),
    }

    # ── Cache check ───────────────────────────────────────────────────────── #
    ck = cache_key("report", payload)
    cached = _cache_get(ck)
    if cached:
        logger.info("Cache HIT for generate-report key=%s", ck[:16])
        return jsonify(cached), 200

    # ── Build prompt ──────────────────────────────────────────────────────── #
    generated_at = datetime.now(timezone.utc).isoformat()
    try:
        template = load_prompt("generate_report_prompt.txt")
    except FileNotFoundError:
        logger.error("Prompt template not found: generate_report_prompt.txt")
        result = {**FALLBACK_REPORT, "generated_at": generated_at}
        return jsonify(result), 200

    prompt = template.format(**payload, generated_at=generated_at)

    # ── Call Groq ─────────────────────────────────────────────────────────── #
    raw = call_groq(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000,
    )

    if raw is None:
        logger.warning("Groq unavailable — returning fallback report")
        result = {**FALLBACK_REPORT, "generated_at": generated_at}
        return jsonify(result), 200

    # ── Parse JSON response ───────────────────────────────────────────────── #
    try:
        # Strip markdown code fences if model wrapped the JSON
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        result = json.loads(clean.strip())

        # Guarantee required fields are present
        result.setdefault("generated_at", generated_at)
        result.setdefault("is_fallback", False)

    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Failed to parse Groq JSON response: %s | raw=%s", exc, raw[:200])
        result = {**FALLBACK_REPORT, "generated_at": generated_at}
        return jsonify(result), 200

    # ── Cache & return ────────────────────────────────────────────────────── #
    _cache_set(ck, result)
    return jsonify(result), 200
