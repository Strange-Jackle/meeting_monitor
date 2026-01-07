import asyncio
import logging
from app.modules.intelligence.web_insight_service import WebInsightService

# Configure logging to see the error
logging.basicConfig(level=logging.DEBUG)

async def test():
    print("Initializing service...")
    try:
        s = WebInsightService()
        print("Service initialized. Fetching insight...")
        result = await s.get_entity_insights_async("Microsoft Azure", "product")
        print("Result:", result)
    except Exception as e:
        print("CRITICAL ERROR:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
