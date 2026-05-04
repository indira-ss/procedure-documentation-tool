import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

class GroqClient:
    def __init__(self):
        self.api_key = os.getenv("api key")
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def generate(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        retries = 3
        wait = 2

        for i in range(retries):
            try:
                response = requests.post(self.url, headers=headers, json=data)
                response.raise_for_status()

                result = response.json()
                return result["choices"][0]["message"]["content"]

            except Exception as e:
                print(f"Error (try {i+1}):", e)

                if i < retries - 1:
                    time.sleep(wait)
                    wait *= 2
                else:
                    return "❌ Failed after 3 attempts"