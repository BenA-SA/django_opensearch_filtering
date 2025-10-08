from django import forms
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

    # Pagination defaults
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100

    def get_form_class(self):
        """
        Get a form class for this filter set.

        Overrides the parent method to add sorting and pagination fields.

        Returns:
            A Django form class
        """
        form_fields = {}

        # Add filter fields
        for name, filter_obj in self.filters.items():
            form_fields[name] = filter_obj.get_form_field()

        # Add sorting field
        form_fields["sort"] = forms.ChoiceField(
            choices=self.SORT_CHOICES,
            required=False,
            label="Sort by",
            widget=forms.Select(attrs={"class": "form-select"}),
        )

        # Add pagination fields
        form_fields["page"] = forms.IntegerField(
            min_value=1,
            required=False,
            initial=1,
            label="Page",
            widget=forms.NumberInput(attrs={"class": "form-control"}),
        )

        form_fields["page_size"] = forms.IntegerField(
            min_value=1,
            max_value=self.MAX_PAGE_SIZE,
            required=False,
            initial=self.DEFAULT_PAGE_SIZE,
            label="Items per page",
            widget=forms.NumberInput(attrs={"class": "form-control"}),
        )

        return type(
            f"{self.__class__.__name__}Form",
            (forms.Form,),
            form_fields,
        )

    def filter(self, search: Search) -> Search:
        """
        Apply all filters to the search.

        This overrides the parent method to handle special cases
        like price_min and price_max, and to apply sorting.

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

        # Apply sorting if specified
        if self.data.get("sort"):
            sort_field = self.data["sort"]
            filtered_search = filtered_search.sort(sort_field)

        return filtered_search

    def search(self) -> Search:
        """
        Get a filtered and paginated search for the document.

        Overrides the parent method to apply pagination.

        Returns:
            A filtered and paginated search object
        """
        # Get the base search object
        search = self.document.search()

        # Apply filters and sorting
        search = self.filter(search)

        # Apply pagination if specified
        page = self.data.get("page", 1)
        if not page or page < 1:
            page = 1

        page_size = self.data.get("page_size", self.DEFAULT_PAGE_SIZE)
        if not page_size or page_size < 1:
            page_size = self.DEFAULT_PAGE_SIZE
        elif page_size > self.MAX_PAGE_SIZE:
            page_size = self.MAX_PAGE_SIZE

        # Calculate start and end indices for pagination
        start = (page - 1) * page_size
        end = start + page_size

        # Apply pagination
        search = search[start:end]

        return search  # noqa: RET504
