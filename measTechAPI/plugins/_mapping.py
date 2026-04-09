"""Common uploader mapping for ontology plugins."""

BASE_MAPPING = {
    "iri": {"type": "keyword"},
    "curie": {"type": "keyword"},
    "label": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
    "synonyms": {"type": "text"},
    "definition": {"type": "text"},
    "parents": {"type": "keyword"},
    "ontology": {"type": "keyword"},
    "ontologies": {"type": "keyword"},
    "source": {"type": "keyword"},
    "is_obsolete": {"type": "boolean"},
    "mapped_canonical_id": {"type": "keyword"},
    "equivalent_ids": {"type": "keyword"},
    "source_ids": {"type": "object", "enabled": True},
    "ontology_terms": {"type": "object", "enabled": True},
}
