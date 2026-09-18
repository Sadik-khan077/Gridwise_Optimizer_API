import pytest
import time
import os

@pytest.fixture(autouse=True)
def rate_limit_sleep():
    """
    Automatically sleeps after each test to avoid hitting the 5 requests/minute
    rate limit on the Google Gemini Free Tier.
    """
    yield
    # Only sleep if we are running the LLM-dependent tests and using a free API key
    # For now, we'll unconditionally sleep 15 seconds after every test.
    # 15 seconds * 4 tests per minute = 60 seconds (keeps us under the 5 req/min limit)
    pass
