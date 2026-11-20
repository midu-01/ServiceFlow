from unittest.mock import AsyncMock, MagicMock, patch
import pytest


@pytest.fixture(autouse=True)
def mock_external_brokers_in_tests():
    """Mocks outbound Redis and Celery network calls during test runs.
    
    This prevents 30-second TCP connection timeouts when tests execute without
    a live Redis broker running on the local host machine.
    """
    with patch("app.realtime.publisher.event_publisher.publish_event", new_callable=AsyncMock) as mock_pub, \
         patch("app.workers.tasks.request_tasks.process_service_request.apply_async", return_value=MagicMock()) as mock_celery:
        yield {
            "mock_pub": mock_pub,
            "mock_celery": mock_celery,
        }
