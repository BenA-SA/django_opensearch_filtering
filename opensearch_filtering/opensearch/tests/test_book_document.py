import logging

import pytest
from django_opensearch_dsl.registries import registry

from opensearch_filtering.opensearch.documents import BookDocument
from opensearch_filtering.opensearch.models import Book
from opensearch_filtering.opensearch.models import Page

logger = logging.getLogger(__name__)


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


@pytest.mark.django_db
class TestBookDocument:
    @pytest.fixture(autouse=True)
    def _setup_index(self, setup_opensearch):
        # Runs before every test in this class
        pass

    def test_book_document(self):
        book = Book.objects.create(
            title="Test Book",
            author="Author Name",
            publication_date="2024-01-01",
            price=19.99,
        )

        # Create pages
        page_one = Page.objects.create(book=book, number=1, text="Page one text")
        page_two = Page.objects.create(book=book, number=2, text="Page two text")

        BookDocument().update([book], action="index")
        BookDocument._index.refresh()  # noqa: SLF001

        # Fetch the document from the index
        doc = BookDocument.search().query("match", id=book.id).execute()[0]

        # Assert fields
        assert doc.title == book.title
        assert doc.author == book.author
        assert doc.price == book.price
        assert len(doc.pages) == book.pages.count()

        assert {"number": page_one.number, "text": page_one.text} in doc.pages
        assert {"number": page_two.number, "text": page_two.text} in doc.pages
