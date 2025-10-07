from django_opensearch_dsl.search import Search

from opensearch_filtering.filters import CharFilter
from opensearch_filtering.filters import DateFilter
from opensearch_filtering.filters import DocumentFilterSet
from opensearch_filtering.filters import NumericFilter
from opensearch_filtering.opensearch.documents import BookDocument


class BookDocumentFilterSet(DocumentFilterSet):
    """Filter set for BookDocument."""

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
