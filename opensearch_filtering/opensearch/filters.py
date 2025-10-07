from django_opensearch_dsl.search import Search

from opensearch_filtering.filters import CharFilter
from opensearch_filtering.filters import DateFilter
from opensearch_filtering.filters import DocumentFilterSet
from opensearch_filtering.filters import NumericFilter
from opensearch_filtering.opensearch.documents import BookDocument


class BookDocumentFilterSet(DocumentFilterSet):
    """Filter set for BookDocument."""

    document = BookDocument

    title = CharFilter(field_name="title", lookup_expr="match", label="Title")
    author = CharFilter(field_name="author", lookup_expr="match", label="Author")
    publication_date = DateFilter(
        field_name="publication_date",
        label="Publication Date",
    )
    price = NumericFilter(field_name="price", label="Price")
    price_min = NumericFilter(field_name="price", lookup_expr="gte", label="Min Price")
    price_max = NumericFilter(field_name="price", lookup_expr="lte", label="Max Price")

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
        # Create a new empty search object
        filtered_search = search

        # Handle price range as a special case
        if "price" not in self.data or not self.data["price"]:
            # Check if price_min or price_max are in the data and have values
            has_price_min = (
                "price_min" in self.data and self.data["price_min"] is not None
            )
            has_price_max = (
                "price_max" in self.data and self.data["price_max"] is not None
            )

            if has_price_min or has_price_max:
                range_params = {}
                if has_price_min:
                    range_params["gte"] = float(self.data["price_min"])
                if has_price_max:
                    range_params["lte"] = float(self.data["price_max"])

                if range_params:
                    filtered_search = filtered_search.query("range", price=range_params)

        # Apply all other filters
        for name, filter_obj in self.filters.items():
            # Skip price_min and price_max as they're handled separately
            if name in ("price_min", "price_max"):
                continue

            # Only apply if the filter has a value
            if name in self.data and self.data[name] not in (None, ""):
                filtered_search = filter_obj.filter(filtered_search, self.data[name])

        return filtered_search
