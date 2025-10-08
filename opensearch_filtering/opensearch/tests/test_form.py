"""Tests for the form generation functionality."""

import pytest
from django import forms

from opensearch_filtering.opensearch.documents import BookDocument
from opensearch_filtering.opensearch.filters import BookDocumentFilterSet
from opensearch_filtering.opensearch.models import Book


@pytest.mark.django_db
class TestBookDocumentFilterSetForm:
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

    def test_form_generation(self):
        """Test that a form can be generated from the filterset."""
        # Create a filterset
        filter_set = BookDocumentFilterSet()

        # Get a form
        form = filter_set.get_form()

        # Check that the form is a Form instance
        assert isinstance(form, forms.Form)

        # Check that the form has the expected fields
        expected_fields = [
            "title",
            "author",
            "publication_date",
            "price",
            "price_min",
            "price_max",
        ]
        for field_name in expected_fields:
            assert field_name in form.fields

        # Check field types
        assert isinstance(form.fields["title"], forms.CharField)
        assert isinstance(form.fields["author"], forms.CharField)
        assert isinstance(form.fields["publication_date"], forms.DateField)
        assert isinstance(form.fields["price"], forms.FloatField)
        assert isinstance(form.fields["price_min"], forms.FloatField)
        assert isinstance(form.fields["price_max"], forms.FloatField)

    def test_form_with_data(self):
        """Test that a form can be initialized with data."""
        # Create data
        data = {
            "title": "Python",
            "price_min": "20.0",
            "price_max": "50.0",
        }

        # Create a filterset with data
        filter_set = BookDocumentFilterSet(data=data)

        # Get a form
        form = filter_set.get_form()

        # Check that the form is bound
        assert form.is_bound

        # Check that the form has the expected data
        assert form.data["title"] == "Python"
        assert form.data["price_min"] == "20.0"
        assert form.data["price_max"] == "50.0"

    def test_form_filtering_title(self):
        """Test that the form correctly filters by title."""
        form_class = BookDocumentFilterSet().get_form_class()
        form = form_class(data={"title": "Python"})
        assert form.is_valid()

        # Use the form's cleaned_data to create a filter_set and execute search
        filter_set = BookDocumentFilterSet(data=form.cleaned_data)
        results = filter_set.search().execute()

        # Should match book1, book3, and book4 but not book2
        expected_matches = 3
        assert len(results) == expected_matches
        titles = [result.title for result in results]
        assert self.book1.title in titles
        assert self.book2.title not in titles
        assert self.book3.title in titles
        assert self.book4.title in titles

    def test_form_filtering_author(self):
        """Test that the form correctly filters by author."""
        form_class = BookDocumentFilterSet().get_form_class()
        form = form_class(data={"author": "Jane"})
        assert form.is_valid()

        # Use the form's cleaned_data to create a filter_set and execute search
        filter_set = BookDocumentFilterSet(data=form.cleaned_data)
        results = filter_set.search().execute()

        # Should match book2 and book4 but not book1 or book3
        expected_matches = 2
        assert len(results) == expected_matches
        titles = [result.title for result in results]
        assert self.book1.title not in titles
        assert self.book2.title in titles
        assert self.book3.title not in titles
        assert self.book4.title in titles

    def test_form_filtering_exact_price(self):
        """Test that the form correctly filters by exact price."""
        form_class = BookDocumentFilterSet().get_form_class()
        form = form_class(data={"price": "29.99"})
        assert form.is_valid()

        # Use the form's cleaned_data to create a filter_set and execute search
        filter_set = BookDocumentFilterSet(data=form.cleaned_data)
        results = filter_set.search().execute()

        # Should match book1 but not book2, book3, or book4
        expected_matches = 1
        assert len(results) == expected_matches
        assert results[0].title == self.book1.title

    def test_form_filtering_price_range(self):
        """Test that the form correctly filters by price range."""
        form_class = BookDocumentFilterSet().get_form_class()
        form = form_class(data={"price_min": "35.0", "price_max": "45.0"})
        assert form.is_valid()

        # Use the form's cleaned_data to create a filter_set and execute search
        filter_set = BookDocumentFilterSet(data=form.cleaned_data)
        results = filter_set.search().execute()

        # Should match book2 but not book1, book3, or book4
        assert len(results) == 1
        assert results[0].title == self.book2.title

    def test_form_filtering_publication_date(self):
        """Test that the form correctly filters by publication date."""
        form_class = BookDocumentFilterSet().get_form_class()
        form = form_class(data={"publication_date": "2023-02-01"})
        assert form.is_valid()

        # Use the form's cleaned_data to create a filter_set and execute search
        filter_set = BookDocumentFilterSet(data=form.cleaned_data)
        results = filter_set.search().execute()

        # Should match book2 but not book1, book3, or book4
        assert len(results) == 1
        assert results[0].title == self.book2.title

    def test_form_filtering_multiple_criteria(self):
        """Test that the form correctly filters by multiple criteria."""
        form_class = BookDocumentFilterSet().get_form_class()
        form = form_class(data={"title": "Python", "author": "Jane"})
        assert form.is_valid()

        # Use the form's cleaned_data to create a filter_set and execute search
        filter_set = BookDocumentFilterSet(data=form.cleaned_data)
        results = filter_set.search().execute()

        # Should match book4 but not book1, book2, or book3
        assert len(results) == 1
        assert results[0].title == self.book4.title
