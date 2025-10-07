from django_opensearch_dsl import Document
from django_opensearch_dsl import fields
from django_opensearch_dsl.registries import registry

from .models import Book
from .models import Page


@registry.register_document
class BookDocument(Document):
    pages = fields.ObjectField(
        properties={"number": fields.IntegerField(), "text": fields.TextField()},
    )
    title = fields.TextField(attr="title")
    author = fields.TextField(attr="author")
    publication_date = fields.DateField(attr="publication_date")
    price = fields.FloatField(attr="price")

    class Index:
        name = "books"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }

    class Django:
        model = Book
        fields = ["id"]

    @staticmethod
    def get_instances_from_related(related_instance):
        if isinstance(related_instance, Page):
            return related_instance.book
        return []
