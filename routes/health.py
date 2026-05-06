from flask import Blueprint, jsonify
import time

health_bp = Blueprint("health", __name__)

start_time = time.time()

@health_bp.route("/health", methods=["GET"])
def health():
    uptime = time.time() - start_time
    return jsonify({
        "status": "UP",
        "uptime_seconds": int(uptime)
    })