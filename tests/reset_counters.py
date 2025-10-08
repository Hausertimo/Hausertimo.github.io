"""
Quick script to reset Redis counters to new initial values
"""
import redis
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to Redis
redis_url = os.getenv('REDIS_URL')
if not redis_url:
    print("No REDIS_URL found!")
    exit(1)

try:
    client = redis.from_url(redis_url, decode_responses=True)

    # Set new values
    client.set('products_searched', 703)
    client.set('norms_scouted', 6397)
    client.set('monthly_users', 413)

    # Verify
    print("Counters reset successfully:")
    print(f"Products Searched: {client.get('products_searched')}")
    print(f"Norms Scouted: {client.get('norms_scouted')}")
    print(f"Monthly Users: {client.get('monthly_users')}")

except Exception as e:
    print(f"Error: {e}")