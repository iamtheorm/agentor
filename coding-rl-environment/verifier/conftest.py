import pytest
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    """
    Creates a session-scoped event loop to prevent 'bound to a different event loop'
    errors when using global async SQLAlchemy engines or Redis clients.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
