from flask import Blueprint, jsonify
import time

health_bp = Blueprint("health", __name__)

# Track when service started
start_time = time.time()

@health_bp.route('/health', methods=['GET'])
def health():
    uptime = time.time() - start_time

    return jsonify({
        "status": "UP",
        "service": "AI Service",
        "uptime_seconds": int(uptime)
    })