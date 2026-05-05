from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()


# ---------- Request Model ----------
class ReportRequest(BaseModel):
    topic: str


# ---------- Response Model ----------
class ReportResponse(BaseModel):
    title: str
    summary: str
    overview: str
    key_items: List[str]
    recommendations: List[str]


# ---------- POST API ----------
@app.post("/generate-report", response_model=ReportResponse)
def generate_report(request: ReportRequest):
    topic = request.topic

    # --- AI-like structured output (you can replace with LLM/Groq/OpenAI later) ---
    response = {
        "title": f"Report on {topic}",

        "summary": f"This report provides a concise analysis of {topic}, highlighting important insights and outcomes.",

        "overview": f"The topic '{topic}' is analyzed based on available data, trends, and key factors affecting its performance or behavior.",

        "key_items": [
            f"Main factor influencing {topic}",
            "Current trends in {topic}",
            "Challenges related to {topic}",
            "Opportunities in {topic}"
        ],

        "recommendations": [
            f"Improve data collection for better insights on {topic}",
            f"Focus on optimization strategies for {topic}",
            f"Monitor changes regularly in {topic}"
        ]
    }

    return response