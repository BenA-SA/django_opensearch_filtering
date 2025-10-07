import logging

import pytest

from opensearch_filtering.opensearch.documents import BookDocument
from opensearch_filtering.opensearch.models import Book
from opensearch_filtering.opensearch.models import Page

logger = logging.getLogger(__name__)


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
