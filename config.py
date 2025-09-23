import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', 'your-api-key-here')
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Default AI Model Settings
DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.8
DEFAULT_FREQUENCY_PENALTY = 0.6
DEFAULT_PRESENCE_PENALTY = 0.1