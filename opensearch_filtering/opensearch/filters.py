from opensearch_filtering.filters import CharFilter
from opensearch_filtering.filters import DateFilter
from opensearch_filtering.filters import DocumentFilterSet
from opensearch_filtering.filters import NumericFilter
from opensearch_filtering.filters import RangeFilter
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
    price_exact = NumericFilter(field_name="price", label="Price")
    price = RangeFilter(field_name="price", label="Price Range")

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
