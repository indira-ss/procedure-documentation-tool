from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("gsk_Z4cY8wyaIw2eQty93kGmWGdyb3FY12Zgc0nFwrebUAkrnjcBkHKks"))

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": "Explain AI in one line"}]
)

print(response.choices[0].message.content)