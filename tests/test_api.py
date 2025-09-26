#!/usr/bin/env python3
"""
Test script for OpenRouter API integration
Usage: python test_api.py
"""

import os
import requests
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in parent directory (Website folder)
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")
else:
    # Try current directory
    load_dotenv()
    print("Looking for .env in current directory")

# ANSI color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_success(text):
    print(f"{GREEN}[OK] {text}{RESET}")

def print_error(text):
    print(f"{RED}[ERROR] {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}[WARNING] {text}{RESET}")

def test_api_key():
    """Test if API key is present and valid format"""
    print_header("Testing API Key Configuration")

    api_key = os.environ.get("openrouter")

    if not api_key:
        print_error("API key not found in environment variables!")
        print("  Set it with: export openrouter='your-api-key-here'")
        print("  On Windows: set openrouter=your-api-key-here")
        return None

    print_success(f"API key found (length: {len(api_key)} chars)")

    # Check API key format (OpenRouter keys typically start with 'sk-')
    if api_key.startswith('sk-'):
        print_success("API key format looks correct (starts with 'sk-')")
    else:
        print_warning("API key doesn't start with 'sk-' - verify it's correct")

    # Hide most of the key for security
    masked_key = api_key[:10] + '...' + api_key[-4:] if len(api_key) > 14 else api_key[:5] + '...'
    print(f"  Masked key: {masked_key}")

    return api_key

def test_direct_api_call(api_key):
    """Test direct OpenRouter API call"""
    print_header("Testing Direct API Call to OpenRouter")

    url = 'https://openrouter.ai/api/v1/chat/completions'

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://normscout.fly.dev",
        "X-Title": "NormScout Test",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Reply with a simple greeting."
            },
            {
                "role": "user",
                "content": "Hello, this is a test message. Please confirm you received this."
            }
        ],
        "temperature": 0.3,
        "max_tokens": 50
    }

    print(f"Endpoint: {url}")
    print(f"Model: {payload['model']}")
    print("Sending test request...")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        print(f"\nResponse Status Code: {response.status_code}")

        if response.status_code == 200:
            print_success("API call successful!")
            result = response.json()

            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"\nAI Response: {content}")
                return True
            else:
                print_error("Unexpected response format")
                print(json.dumps(result, indent=2))
                return False
        else:
            print_error(f"API call failed with status {response.status_code}")
            print(f"Response: {response.text}")

            # Try to parse error
            try:
                error_data = response.json()
                if 'error' in error_data:
                    print(f"\nError details:")
                    print(f"  Code: {error_data['error'].get('code', 'unknown')}")
                    print(f"  Message: {error_data['error'].get('message', 'unknown')}")
            except:
                pass

            return False

    except requests.exceptions.Timeout:
        print_error("Request timed out after 30 seconds")
        return False
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False

def test_local_flask_app():
    """Test local Flask app if running"""
    print_header("Testing Local Flask App")

    local_url = "http://localhost:8080/api/run"

    test_data = {
        "product": "Bluetooth Speaker",
        "country": "eu"
    }

    print(f"Testing endpoint: {local_url}")
    print(f"Test data: {json.dumps(test_data, indent=2)}")

    try:
        response = requests.post(local_url, json=test_data, timeout=35)

        print(f"\nResponse Status Code: {response.status_code}")

        result = response.json()

        if result.get('status') == 'success':
            print_success("Local app API call successful!")
            print(f"\nResponse preview (first 200 chars):")
            print(result['result'][:200] + "...")
            return True
        else:
            print_error(f"Local app returned error status: {result.get('status')}")
            print(f"Error: {result.get('error', 'unknown')}")
            return False

    except requests.exceptions.ConnectionError:
        print_warning("Could not connect to local Flask app")
        print("  Make sure it's running: python app.py")
        return False
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False

def main():
    print(f"\n{BLUE}OpenRouter API Test Script{RESET}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Test 1: Check API key
    api_key = test_api_key()
    if not api_key:
        print("\n[ERROR] Cannot proceed without API key")
        sys.exit(1)

    # Test 2: Direct API call
    api_success = test_direct_api_call(api_key)

    if api_success:
        print(f"\n{GREEN}[OK] Direct API test passed!{RESET}")
    else:
        print(f"\n{RED}[ERROR] Direct API test failed!{RESET}")
        print("\nTroubleshooting steps:")
        print("1. Verify your API key is correct")
        print("2. Check your OpenRouter account has credits")
        print("3. Ensure the API key has proper permissions")
        print("4. Visit https://openrouter.ai/account to check your account")

    # Test 3: Local Flask app (optional)
    print("\n" + "="*60)
    test_local_flask_app()

    # Summary
    print_header("Test Summary")
    if api_success:
        print_success("OpenRouter API is working correctly!")
        print("\nNext steps:")
        print("1. Deploy to Fly.io: fly deploy")
        print("2. Set the secret on Fly.io: fly secrets set openrouter='your-api-key-here'")
        print("3. Check logs: fly logs")
    else:
        print_error("OpenRouter API tests failed - see errors above")

if __name__ == "__main__":
    main()