"""
Filters for Opensearch documents, inspired by django-filter.

This module provides a filtering system for Opensearch documents similar to
django-filter, but designed to work with Opensearch queries instead of Django ORM.
"""

from abc import ABC
from abc import abstractmethod
from datetime import datetime
from typing import Any

from django_opensearch_dsl import Document
from django_opensearch_dsl.search import Search


class BaseFilter(ABC):
    """Base class for all filters."""

    def __init__(self, field_name: str):
        """
        Initialize the filter.

        Args:
            field_name: The name of the field to filter on
        """
        self.field_name = field_name

    @abstractmethod
    def filter(self, search: Search, value: Any) -> Search:
        """
        Apply the filter to the search.

        Args:
            search: The search object to filter
            value: The value to filter by

        Returns:
            The filtered search object
        """


class CharFilter(BaseFilter):
    """Filter for character fields."""

    def __init__(self, field_name: str, lookup_expr: str = "match"):
        """
        Initialize the filter.

        Args:
            field_name: The name of the field to filter on
            lookup_expr: The lookup expression to use (match, term, wildcard, etc.)
        """
        super().__init__(field_name)
        self.lookup_expr = lookup_expr

    def filter(self, search: Search, value: str) -> Search:
        """
        Apply the filter to the search.

        Args:
            search: The search object to filter
            value: The value to filter by

        Returns:
            The filtered search object
        """
        if not value:
            return search

        if self.lookup_expr == "match":
            return search.query("match", **{self.field_name: value})
        if self.lookup_expr == "term":
            return search.query("term", **{self.field_name: value})
        if self.lookup_expr == "wildcard":
            return search.query("wildcard", **{self.field_name: f"*{value}*"})
        return search.query(self.lookup_expr, **{self.field_name: value})


class NumericFilter(BaseFilter):
    """Filter for numeric fields."""

    def __init__(self, field_name: str, lookup_expr: str = "term"):
        """
        Initialize the filter.

        Args:
            field_name: The name of the field to filter on
            lookup_expr: The lookup expression to use (term, range, etc.)
        """
        super().__init__(field_name)
        self.lookup_expr = lookup_expr

    def filter(self, search: Search, value: float) -> Search:  # noqa: PLR0911
        """
        Apply the filter to the search.

        Args:
            search: The search object to filter
            value: The value to filter by

        Returns:
            The filtered search object
        """
        if value is None:
            return search

        if self.lookup_expr == "term":
            return search.query("term", **{self.field_name: value})
        if self.lookup_expr == "gt":
            return search.query("range", **{self.field_name: {"gt": value}})
        if self.lookup_expr == "gte":
            return search.query("range", **{self.field_name: {"gte": value}})
        if self.lookup_expr == "lt":
            return search.query("range", **{self.field_name: {"lt": value}})
        if self.lookup_expr == "lte":
            return search.query("range", **{self.field_name: {"lte": value}})
        return search.query(self.lookup_expr, **{self.field_name: value})


class DateFilter(BaseFilter):
    """Filter for date fields."""

    def __init__(self, field_name: str, lookup_expr: str = "term"):
        """
        Initialize the filter.

        Args:
            field_name: The name of the field to filter on
            lookup_expr: The lookup expression to use (term, range, etc.)
        """
        super().__init__(field_name)
        self.lookup_expr = lookup_expr

    def filter(self, search: Search, value: str | datetime) -> Search:  # noqa: PLR0911
        """
        Apply the filter to the search.

        Args:
            search: The search object to filter
            value: The value to filter by

        Returns:
            The filtered search object
        """
        if not value:
            return search

        if self.lookup_expr == "term":
            return search.query("term", **{self.field_name: value})
        if self.lookup_expr == "gt":
            return search.query("range", **{self.field_name: {"gt": value}})
        if self.lookup_expr == "gte":
            return search.query("range", **{self.field_name: {"gte": value}})
        if self.lookup_expr == "lt":
            return search.query("range", **{self.field_name: {"lt": value}})
        if self.lookup_expr == "lte":
            return search.query("range", **{self.field_name: {"lte": value}})
        return search.query(self.lookup_expr, **{self.field_name: value})


class BooleanFilter(BaseFilter):
    """Filter for boolean fields."""

    def filter(self, search: Search, value: bool) -> Search:  # noqa: FBT001
        """
        Apply the filter to the search.

        Args:
            search: The search object to filter
            value: The value to filter by

        Returns:
            The filtered search object
        """
        if value is None:
            return search

        return search.query("term", **{self.field_name: value})


class FilterSet:
    """Base class for filter sets."""

    def __init__(self, data: dict[str, Any] | None = None):
        """
        Initialize the filter set.

        Args:
            data: The data to filter by
        """
        self.data = data or {}
        self.filters = self.get_filters()

    @classmethod
    def get_filters(cls) -> dict[str, BaseFilter]:
        """
        Get all filters defined on the class.

        Returns:
            A dictionary of filter names to filter objects
        """
        filters = {}
        for name, obj in cls.__dict__.items():
            if isinstance(obj, BaseFilter):
                filters[name] = obj  # noqa: PERF403
        return filters

    def filter(self, search: Search) -> Search:
        """
        Apply all filters to the search.

        Args:
            search: The search object to filter

        Returns:
            The filtered search object
        """
        for name, filter_obj in self.filters.items():
            if name in self.data:
                search = filter_obj.filter(search, self.data[name])
        return search


class DocumentFilterSet(FilterSet):
    """Base class for document filter sets."""

    document: type[Document] = None

    def __init__(self, data: dict[str, Any] | None = None):
        """
        Initialize the document filter set.

        Args:
            data: The data to filter by
        """
        super().__init__(data)
        if self.document is None:
            error_message = "DocumentFilterSet requires a document class"
            raise ValueError(error_message)

    def search(self) -> Search:
        """
        Get a filtered search for the document.

        Returns:
            A filtered search object
        """
        search = self.document.search()
        return self.filter(search)


class BookDocumentFilterSet(DocumentFilterSet):
    """Filter set for BookDocument."""

    from opensearch_filtering.opensearch.documents import BookDocument  # noqa: PLC0415

    document = BookDocument

    title = CharFilter(field_name="title", lookup_expr="match")
    author = CharFilter(field_name="author", lookup_expr="match")
    publication_date = DateFilter(field_name="publication_date")
    price = NumericFilter(field_name="price")
    price_min = NumericFilter(field_name="price", lookup_expr="gte")
    price_max = NumericFilter(field_name="price", lookup_expr="lte")

    def filter(self, search: Search) -> Search:
        """
        Apply all filters to the search.

        This overrides the parent method to handle special cases
        like price_min and price_max.

        Args:
            search: The search object to filter

        Returns:
            The filtered search object
        """
        for name, filter_obj in self.filters.items():
            # Skip price_min and price_max if price is provided
            if name in ("price_min", "price_max") and "price" in self.data:
                continue

            if name in self.data:
                search = filter_obj.filter(search, self.data[name])

        return search
