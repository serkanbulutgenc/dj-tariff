from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from .models import TariffNode


@registry.register_document
class TariffNodeDocument(Document):
    # Custom analyzers/tokenizers for partial code matches (prefix matching)
    code = fields.KeywordField(
        fields={
            "raw": fields.KeywordField(),
            "suggest": fields.TextField(analyzer="edge_ngram_analyzer"),
        },
    )
    name = fields.TextField(analyzer="turkish", fields={"raw": fields.KeywordField()})
    node_type = fields.KeywordField()
    depth = fields.IntegerField()
    path = fields.KeywordField()
    is_leaf = fields.BooleanField()

    class Index:
        name = "tariff_nodes"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "edge_ngram_analyzer": {
                        "type": "custom",
                        "tokenizer": "edge_ngram_tokenizer",
                        "filter": ["lowercase"],
                    },
                },
                "tokenizer": {
                    "edge_ngram_tokenizer": {
                        "type": "edge_ngram",
                        "min_gram": 2,
                        "max_gram": 12,
                        "token_chars": ["digit", "letter"],
                    },
                },
            },
        }

    class Django:
        model = TariffNode
        fields = ["id"]
