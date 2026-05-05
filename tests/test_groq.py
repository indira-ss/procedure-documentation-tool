import os
os.environ["GROQ_API_KEY"] = ""  # paste your new key here

from services.groq_client import call_groq

result = call_groq("Return this exact JSON: {\"status\": \"ok\"}")

if result:
    print("✅ Groq is working!")
    print(result)
else:
    print("❌ Groq failed")