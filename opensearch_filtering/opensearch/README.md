# Opensearch Filtering

A filtering system for Opensearch documents inspired by django-filter, but designed to work with Opensearch queries instead of Django ORM.

## Overview

This library provides a way to filter Opensearch documents similar to how django-filter works with Django models. It allows you to define filter sets with various filter types and apply them to Opensearch searches.

## Installation

The filtering system is included in the opensearch app of this project. No additional installation is required.

## Usage

### Basic Usage

```python
from opensearch_filtering.opensearch.filters import BookDocumentFilterSet

# Create a filter set with filter parameters
filter_set = BookDocumentFilterSet(data={
    "title": "Python",
    "author": "John",
    "price_min": 20.0,
    "price_max": 50.0,
})

# Get filtered search results
results = filter_set.search().execute()

# Process results
for book in results:
    print(f"Title: {book.title}, Author: {book.author}, Price: {book.price}")
```

### Creating Custom Filter Sets

You can create custom filter sets for your own document types:

```python
from opensearch_filtering.opensearch.filters import DocumentFilterSet, CharFilter, NumericFilter, DateFilter

class MyDocumentFilterSet(DocumentFilterSet):
    # Specify the document class
    from my_app.documents import MyDocument
    document = MyDocument

    # Define filters
    name = CharFilter(field_name="name", lookup_expr="match")
    description = CharFilter(field_name="description", lookup_expr="match")
    created_at = DateFilter(field_name="created_at")
    value = NumericFilter(field_name="value")
    value_min = NumericFilter(field_name="value", lookup_expr="gte")
    value_max = NumericFilter(field_name="value", lookup_expr="lte")

    # Optionally override filter method for custom behavior
    def filter(self, search):
        # Custom filtering logic
        return super().filter(search)
```

## Filter Types

The following filter types are available:

### CharFilter

For filtering text fields.

```python
title = CharFilter(field_name="title", lookup_expr="match")
```

Available lookup expressions:
- `match`: Performs a full-text search (default)
- `term`: Exact match
- `wildcard`: Wildcard matching with * characters

### NumericFilter

For filtering numeric fields.

```python
price = NumericFilter(field_name="price")
price_min = NumericFilter(field_name="price", lookup_expr="gte")
price_max = NumericFilter(field_name="price", lookup_expr="lte")
```

Available lookup expressions:
- `term`: Exact match (default)
- `gt`: Greater than
- `gte`: Greater than or equal to
- `lt`: Less than
- `lte`: Less than or equal to

### DateFilter

For filtering date fields.

```python
publication_date = DateFilter(field_name="publication_date")
```

Available lookup expressions:
- `term`: Exact match (default)
- `gt`: Greater than
- `gte`: Greater than or equal to
- `lt`: Less than
- `lte`: Less than or equal to

### BooleanFilter

For filtering boolean fields.

```python
is_active = BooleanFilter(field_name="is_active")
```

## Advanced Usage

### Combining with Other Search Features

You can combine filtering with other Opensearch search features:

```python
# Create a filter set
filter_set = BookDocumentFilterSet(data={"author": "John"})

# Get the filtered search
search = filter_set.search()

# Add additional search features
search = search.sort("publication_date")
search = search.highlight("title")

# Execute the search
results = search.execute()
```

### Custom Filter Logic

You can create custom filter classes by extending `BaseFilter`:

```python
from opensearch_filtering.opensearch.filters import BaseFilter

class CustomFilter(BaseFilter):
    def __init__(self, field_name, custom_param=None):
        super().__init__(field_name)
        self.custom_param = custom_param

    def filter(self, search, value):
        if not value:
            return search

        # Custom filter logic
        return search.query("custom_query", **{self.field_name: value})
```

## Example

Here's a complete example of filtering books:

```python
from opensearch_filtering.opensearch.filters import BookDocumentFilterSet

# Filter books by Python in title, published after 2020, with price between 20 and 50
filter_set = BookDocumentFilterSet(data={
    "title": "Python",
    "publication_date_min": "2020-01-01",
    "price_min": 20.0,
    "price_max": 50.0,
})

# Get filtered search results
results = filter_set.search().execute()

# Process results
for book in results:
    print(f"Title: {book.title}")
    print(f"Author: {book.author}")
    print(f"Publication Date: {book.publication_date}")
    print(f"Price: ${book.price}")
    print("---")
```
