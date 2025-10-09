from django_opensearch_dsl.search import Search

from opensearch_filtering.filters import CharFilter
from opensearch_filtering.filters import DateFilter
from opensearch_filtering.filters import DocumentFilterSet
from opensearch_filtering.filters import NumericFilter
from opensearch_filtering.opensearch.documents import BookDocument


class BookDocumentFilterSet(DocumentFilterSet):
    """Filter set for BookDocument."""

    document = BookDocument

    # Filter fields
    title = CharFilter(field_name="title", lookup_expr="match", label="Title")
    author = CharFilter(field_name="author", lookup_expr="match", label="Author")
    publication_date = DateFilter(
        field_name="publication_date",
        label="Publication Date",
    )
    price = NumericFilter(field_name="price", label="Price")
    price_min = NumericFilter(field_name="price", lookup_expr="gte", label="Min Price")
    price_max = NumericFilter(field_name="price", lookup_expr="lte", label="Max Price")

    # Sorting options
    SORT_CHOICES = [
        ("", "Default"),
        ("title_keyword", "Title (A-Z)"),
        ("-title_keyword", "Title (Z-A)"),
        ("author_keyword", "Author (A-Z)"),
        ("-author_keyword", "Author (Z-A)"),
        ("publication_date", "Publication Date (Oldest first)"),
        ("-publication_date", "Publication Date (Newest first)"),
        ("price", "Price (Low to High)"),
        ("-price", "Price (High to Low)"),
    ]

    def filter(self, search: Search) -> Search:
        """
        Apply all filters to the search.

        This overrides the parent method to handle special cases
        like price_min and price_max before applying standard filters.

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

        # Apply standard filters and sorting via parent class method
        # Skip price_min and price_max as they're handled separately
        original_data = self.data.copy()
        if "price_min" in self.data:
            del self.data["price_min"]
        if "price_max" in self.data:
            del self.data["price_max"]

        # Call parent filter method to apply standard filters and sorting
        filtered_search = super().filter(filtered_search)

        # Restore original data
        self.data = original_data

        return filtered_search
