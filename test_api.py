import asyncio
from openrouter_api import generate_compliance_analysis, call_openrouter_api

async def test_basic_api():
    """Test basic API functionality without OpenRouter key"""
    print("Testing basic API structure...")

    # Test with mock data (will fail without real API key but shows structure)
    try:
        result = await generate_compliance_analysis(
            product="Wireless Bluetooth headphones",
            country="United States"
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Expected error (no API key): {e}")

    print("API structure test complete!")

if __name__ == "__main__":
    asyncio.run(test_basic_api())