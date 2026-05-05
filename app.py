from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq

app = FastAPI()
from dotenv import load_dotenv
load_dotenv()
import os
from groq import Groq

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