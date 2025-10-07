"""Tests for the Opensearch filters."""

import pytest

from opensearch_filtering.opensearch.documents import BookDocument
from opensearch_filtering.opensearch.filters import BookDocumentFilterSet
from opensearch_filtering.opensearch.models import Book


@pytest.mark.django_db
class TestBookDocumentFilterSet:
    @pytest.fixture(autouse=True)
    def _setup_index(self, setup_opensearch):
        # Runs before every test in this class
        pass

    @pytest.fixture(autouse=True)
    def setup_test_books(self, django_db_blocker):
        """
        Create test books for all tests and clean up after each test.
        """
        with django_db_blocker.unblock():
            # Create test books
            book1 = Book.objects.create(
                title="Python Programming",
                author="John Doe",
                publication_date="2023-01-01",
                price=29.99,
            )
            book2 = Book.objects.create(
                title="Django Web Development",
                author="Jane Smith",
                publication_date="2023-02-01",
                price=39.99,
            )
            book3 = Book.objects.create(
                title="Advanced Python",
                author="Bob Johnson",
                publication_date="2023-03-01",
                price=49.99,
            )
            book4 = Book.objects.create(
                title="Python Advanced",
                author="Jane Smith",
                publication_date="2023-03-01",
                price=49.99,
            )

            # Index the books
            BookDocument().update([book1, book2, book3, book4], action="index")
            BookDocument._index.refresh()  # noqa: SLF001

            # Make books available to the test methods
            self.book1 = book1
            self.book2 = book2
            self.book3 = book3
            self.book4 = book4

            yield

            # Clean up after the test
            Book.objects.all().delete()

            # Refresh the index to reflect the deletions
            BookDocument._index.refresh()  # noqa: SLF001

    def test_title_filter(self):
        # Test title filter
        filter_set = BookDocumentFilterSet(data={"title": "Python"})
        results = filter_set.search().execute()

        # Should match book1 and book4 but not book2 or book3
        expected_number_of_results = 3
        assert len(results) == expected_number_of_results
        titles = [result.title for result in results]
        assert self.book1.title in titles
        assert self.book2.title not in titles
        assert self.book3.title in titles
        assert self.book4.title in titles

    def test_author_filter(self):
        # Test author filter
        filter_set = BookDocumentFilterSet(data={"author": "Jane"})
        results = filter_set.search().execute()

        # Should match book2 and book4 but not book1 or book3
        expected_number_of_results = 2
        assert len(results) == expected_number_of_results
        titles = [result.title for result in results]
        assert self.book2.title in titles
        assert self.book4.title in titles

    def test_price_filter(self):
        # Test exact price filter
        filter_set = BookDocumentFilterSet(data={"price": 29.99})
        results = filter_set.search().execute()

        # Should match book1 but not book2, book3, or book4
        assert len(results) == 1
        assert results[0].title == self.book1.title

    def test_price_range_filter(self):
        # Test price range filter
        filter_set = BookDocumentFilterSet(data={"price_min": 35.0, "price_max": 45.0})
        results = filter_set.search().execute()

        # Should match book2 but not book1, book3, or book4
        assert len(results) == 1
        assert results[0].title == self.book2.title

    def test_publication_date_filter(self):
        # Test publication_date filter
        filter_set = BookDocumentFilterSet(data={"publication_date": "2023-02-01"})
        results = filter_set.search().execute()

        # Should match book2 but not book1, book3, or book4
        assert len(results) == 1
        assert results[0].title == self.book2.title

    def test_multiple_filters(self):
        # Test multiple filters
        filter_set = BookDocumentFilterSet(data={"title": "Python", "author": "Jane"})
        results = filter_set.search().execute()

        # Should match book4 but not book1, book2, or book3
        assert len(results) == 1
        assert results[0].title == self.book4.title
