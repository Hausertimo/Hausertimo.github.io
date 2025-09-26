import os
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get API key
api_key = os.environ.get("openrouter")
print(f"API Key: {api_key[:20]}..." if api_key else "NO API KEY FOUND")

# Test OpenRouter API
url = 'https://openrouter.ai/api/v1/chat/completions'
headers = {
    "Authorization": f"Bearer {api_key}",
    "HTTP-Referer": "https://normscout.fly.dev",
    "X-Title": "NormScout",
    "Content-Type": "application/json"
}

data = {
    "model": "openai/gpt-4o-mini",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 10
}

response = requests.post(url, headers=headers, json=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")