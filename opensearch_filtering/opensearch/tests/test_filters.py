"""Tests for the Opensearch filters."""

import logging
from datetime import datetime

import pytest

from opensearch_filtering.opensearch.documents import BookDocument
from opensearch_filtering.opensearch.filters import BookDocumentFilterSet
from opensearch_filtering.opensearch.models import Book

logger = logging.getLogger(__name__)


@pytest.mark.django_db
class TestBookDocumentFilterSet:
    @pytest.fixture(autouse=True)
    def _setup_index(self, setup_opensearch):
        """
        Runs before every test in this class.
        Clears the index to ensure test isolation.
        """
        # Clear the index before running tests in this class
        BookDocument._index.delete()  # noqa: SLF001
        BookDocument.init()

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
        filter_set = BookDocumentFilterSet(data={"price_exact": 29.99})
        results = filter_set.search().execute()

        # Should match book1 but not book2, book3, or book4
        assert len(results) == 1
        assert results[0].title == self.book1.title

    def test_price_range_filter(self):
        # Test price range filter
        filter_set = BookDocumentFilterSet(
            data={"price_min_value": 35.0, "price_max_value": 45.0},
        )
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

    def test_sorting_by_title_asc(self):
        """Test sorting by title in ascending order."""
        filter_set = BookDocumentFilterSet(data={"sort": "title_keyword"})
        results = filter_set.search().execute()

        # All books should be returned, sorted by title (A-Z)
        expected_number_of_results = 4
        assert len(results) == expected_number_of_results
        titles = [result.title for result in results]
        logger.info(f"Titles: {titles}")  # noqa: G004
        expected_order = [
            self.book3.title,  # "Advanced Python"
            self.book2.title,  # "Django Web Development"
            self.book4.title,  # "Python Advanced"
            self.book1.title,  # "Python Programming"
        ]
        assert titles == expected_order

    def test_sorting_by_title_desc(self):
        """Test sorting by title in descending order."""
        filter_set = BookDocumentFilterSet(data={"sort": "-title_keyword"})
        results = filter_set.search().execute()

        # All books should be returned, sorted by title (Z-A)
        expected_number_of_results = 4
        assert len(results) == expected_number_of_results
        titles = [result.title for result in results]
        logger.info(f"Titles: {titles}")  # noqa: G004
        expected_order = [
            self.book1.title,  # "Python Programming"
            self.book4.title,  # "Python Advanced"
            self.book2.title,  # "Django Web Development"
            self.book3.title,  # "Advanced Python"
        ]
        assert titles == expected_order

    def test_sorting_by_price_asc(self):
        """Test sorting by price in ascending order."""
        filter_set = BookDocumentFilterSet(data={"sort": "price"})
        results = filter_set.search().execute()

        # All books should be returned, sorted by price (low to high)
        expected_number_of_results = 4
        assert len(results) == expected_number_of_results
        prices = [result.price for result in results]
        logger.info(f"Prices: {prices}")  # noqa: G004
        expected_order = [
            29.99,
            39.99,
            49.99,
            49.99,
        ]  # book1, book2, book3/book4 (same price)
        assert prices == expected_order

    def test_sorting_by_publication_date_desc(self):
        """Test sorting by publication date in descending order."""
        filter_set = BookDocumentFilterSet(data={"sort": "-publication_date"})
        results = filter_set.search().execute()

        # All books should be returned, sorted by publication date (newest first)
        expected_number_of_results = 4
        assert len(results) == expected_number_of_results
        dates = [result.publication_date for result in results]
        # book3 and book4 have the same date (2023-03-01),
        # then book2 (2023-02-01),
        # then book1 (2023-01-01)
        logger.info(f"Dates: {dates}")  # noqa: G004
        assert dates[0] == dates[1] == datetime(2023, 3, 1)  # noqa: DTZ001
        assert dates[2] == datetime(2023, 2, 1)  # noqa: DTZ001
        assert dates[3] == datetime(2023, 1, 1)  # noqa: DTZ001

    def test_pagination_default(self):
        """Test default pagination (page 1, default page size)."""
        filter_set = BookDocumentFilterSet(data={})
        results = filter_set.search().execute()

        # All books should be returned (default page size is larger than our test data)
        expected_number_of_results = 4
        assert len(results) == expected_number_of_results

    def test_pagination_page_size(self):
        """Test pagination with custom page size."""
        filter_set = BookDocumentFilterSet(data={"page_size": 2})
        results = filter_set.search().execute()

        # Only the first 2 books should be returned
        expected_number_of_results = 2
        assert len(results) == expected_number_of_results

    def test_pagination_second_page(self):
        """Test pagination with second page."""
        # First, get the first page with 2 items
        filter_set = BookDocumentFilterSet(data={"page": 1, "page_size": 2})
        first_page = filter_set.search().execute()
        expected_number_of_results = 2
        assert len(first_page) == expected_number_of_results

        # Then, get the second page with 2 items
        filter_set = BookDocumentFilterSet(data={"page": 2, "page_size": 2})
        second_page = filter_set.search().execute()
        expected_number_of_results = 2
        assert len(second_page) == expected_number_of_results

        # Ensure first and second page have different items
        first_page_ids = [item.id for item in first_page]
        second_page_ids = [item.id for item in second_page]
        assert not set(first_page_ids).intersection(set(second_page_ids))

    def test_pagination_with_sorting(self):
        """Test pagination combined with sorting."""
        filter_set = BookDocumentFilterSet(
            data={"sort": "title_keyword", "page": 1, "page_size": 2},
        )
        results = filter_set.search().execute()

        # Only the first 2 books should be returned, sorted by title
        expected_number_of_results = 2
        assert len(results) == expected_number_of_results
        titles = [result.title for result in results]
        expected_first_two = [
            self.book3.title,  # "Advanced Python"
            self.book2.title,  # "Django Web Development"
        ]
        assert titles == expected_first_two

        # Get the second page
        filter_set = BookDocumentFilterSet(
            data={"sort": "title_keyword", "page": 2, "page_size": 2},
        )
        results = filter_set.search().execute()

        # The next 2 books should be returned, sorted by title
        expected_number_of_results = 2
        assert len(results) == expected_number_of_results
        titles = [result.title for result in results]
        expected_next_two = [
            self.book4.title,  # "Python Advanced"
            self.book1.title,  # "Python Programming"
        ]
        assert titles == expected_next_two
