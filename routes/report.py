from flask import Blueprint, request, jsonify
from services.groq_client import call_groq
from datetime import datetime, timezone
import json, os, re

report_bp = Blueprint('report', __name__)

def load_prompt(data: str) -> str:
    path = os.path.join(os.path.dirname(__file__), '../prompts/generate_report.txt')
    with open(path) as f:
        return f.read().replace('{procedure_data}', data)

@report_bp.route('/generate-report', methods=['POST'])
def generate_report():
    body = request.get_json(silent=True)
    if not body or not body.get('procedure_data'):
        return jsonify({'error': 'procedure_data is required'}), 400

    raw = body['procedure_data'].strip()
    if not raw:
        return jsonify({'error': 'procedure_data cannot be empty'}), 400

    prompt = load_prompt(raw)
    response = call_groq(prompt)

    if response is None:
        return jsonify({
            'title': 'Report Unavailable',
            'summary': 'AI service is temporarily unavailable.',
            'overview': '',
            'key_items': [],
            'recommendations': [],
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'is_fallback': True
        }), 200

    try:
        # Strip markdown fences if Groq wraps in ```json
        clean = re.sub(r'```json|```', '', response).strip()
        parsed = json.loads(clean)
        parsed['generated_at'] = datetime.now(timezone.utc).isoformat()
        parsed['is_fallback'] = False
        return jsonify(parsed), 200
    except json.JSONDecodeError:
        return jsonify({'error': 'Failed to parse AI response', 'is_fallback': True}), 502