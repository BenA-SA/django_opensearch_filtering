import logging
import time

import pytest
from django_opensearch_dsl.registries import registry
from opensearchpy.exceptions import ConnectionError as OpenSearchConnectionError

from opensearch_filtering.users.models import User
from opensearch_filtering.users.tests.factories import UserFactory

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


def wait_for_opensearch(max_retries=30, delay=1):
    """
    Wait for OpenSearch to be ready by attempting to connect with retries.

    Args:
        max_retries: Maximum number of connection attempts
        delay: Delay between retries in seconds

    Returns:
        True if connection successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            # Try to get a document to check connection
            doc = next(iter(registry.get_documents()), None)
            if doc:
                # Just check if we can connect, don't care about the result
                doc._index.exists()  # noqa: SLF001
                logger_message = (
                    f"OpenSearch connection successful after {attempt + 1} attempts"
                )
                logger.info(logger_message)
                return True
            # No documents registered
            return False  # noqa: TRY300
        except OpenSearchConnectionError:
            logger_message = (
                f"Waiting for OpenSearch to be ready... "
                f"(attempt {attempt + 1}/{max_retries})"
            )
            logger.info(logger_message)
            time.sleep(delay)

    logger_message = f"Failed to connect to OpenSearch after {max_retries} attempts"
    logger.warning(logger_message)
    return False


@pytest.fixture(scope="session", autouse=True)
def setup_opensearch(django_db_setup, django_db_blocker):
    """
    Ensures indexes exist and are populated.
    Waits for OpenSearch to be ready before proceeding.
    """
    # Wait for OpenSearch to be ready
    wait_for_opensearch()

    with django_db_blocker.unblock():
        # Delete existing indexes to avoid conflicts
        for doc in registry.get_documents():
            if doc._index.exists():  # noqa: SLF001
                doc._index.delete()  # noqa: SLF001

        # Create new indexes from documents
        for doc in registry.get_documents():
            doc.init()
