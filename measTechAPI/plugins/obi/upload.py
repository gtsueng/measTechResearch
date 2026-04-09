"""BioThings uploader for OBI."""

from biothings.hub.dataload.uploader import BaseSourceUploader


class OBIUploader(BaseSourceUploader):
    name = "obi"
    __metadata__ = {
        "src_name": "obi",
        "src_url": "http://purl.obolibrary.org/obo/obi.owl",
        "license_url": "https://obofoundry.org/ontology/obi.html",
    }

    @classmethod
    def get_mapping(cls):
        return {
            "iri": {"type": "keyword"},
            "curie": {"type": "keyword"},
            "label": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
            },
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
