from flask import Flask, jsonify
from routes.describe import describe_bp
from routes.recommend import recommend_bp
import time
from groq import Groq

import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = Flask(__name__)

start_time = time.time()

app.register_blueprint(describe_bp)
app.register_blueprint(recommend_bp)

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "model": "groq",
        "uptime_seconds": int(time.time() - start_time)
    })

# 🔥 THIS PART WAS MISSING
if __name__ == "__main__":
    app.run(debug=True)