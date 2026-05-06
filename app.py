from flask import Flask

app = Flask(__name__)

from routes.report import report_bp
from routes.health import health_bp

app.register_blueprint(report_bp)
app.register_blueprint(health_bp)

@app.route("/")
def home():
    return {"message": "Server is running"}

if __name__ == "__main__":
    app.run(debug=False, port=5000)
from flask import Flask

app = Flask(__name__)

# 🔐 SECURITY HEADERS (ZAP FIX)
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
app = Flask(__name__)

from routes.health import health_bp
import routes.report

app.register_blueprint(health_bp)
app.register_blueprint(routes.report.report_bp)

@app.route("/")
def home():
    return {"message": "Server is running"}

if __name__ == "__main__":
    app.run(debug=True, port=5000)

if __name__ == "__main__":
    app.run(debug=True)



from dotenv import load_dotenv
load_dotenv()
import os
from groq import Groq
if __name__ == "__main__":
    app.run(debug=True)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class ReportRequest(BaseModel):
    topic: str


@app.post("/generate-report")
def generate_report(request: ReportRequest):

    prompt = f"""
    Generate a structured report on: {request.topic}

    Return JSON with:
    - title
    - summary
    - overview (paragraph)
    - key_items (list)
    - recommendations (list)
    """

    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "report": response.choices[0].message.content
    }