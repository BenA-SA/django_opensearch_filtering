import pytest
from django_opensearch_dsl.registries import registry

from opensearch_filtering.users.models import User
from opensearch_filtering.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture(scope="session", autouse=True)
def setup_opensearch(django_db_setup, django_db_blocker):
    """
    Ensures indexes exist and are populated.
    """

    with django_db_blocker.unblock():
        # Delete existing indexes to avoid conflicts
        for doc in registry.get_documents():
            if doc._index.exists():  # noqa: SLF001
                doc._index.delete()  # noqa: SLF001

        # Create new indexes from documents
        for doc in registry.get_documents():
            doc.init()
