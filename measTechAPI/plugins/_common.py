"""Generic parser helpers for ontology CSV plugin parsers."""

import csv
import json
import sys
from pathlib import Path


def _maximize_csv_field_limit():
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit = limit // 10


def split_pipe(value):
    if not value:
        return []
    return [part.strip() for part in value.split("|") if part.strip()]


def load_map(data_folder, filename):
    p = Path(data_folder) / filename
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def read_rows(csv_path):
    _maximize_csv_field_limit()
    with Path(csv_path).open("r", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle)


def onto_from_iri(iri):
    if "/obo/MMO_" in iri:
        return "MMO"
    if "/obo/CHMO_" in iri:
        return "CHMO"
    if "/obo/OBI_" in iri:
        return "OBI"
    if "bioassayontology.org/bao#BAO_" in iri:
        return "BAO"
    if "/efo/EFO_" in iri:
        return "EFO"
    if "edamontology.org/topic_" in iri:
        return "EDAMT"
    if "/obo/NCIT_" in iri or "Thesaurus.owl#C" in iri:
        return "NCIT"
    return "UNKNOWN"


def curie_from_iri(iri):
    if "/obo/MMO_" in iri:
        return "MMO:" + iri.rsplit("MMO_", 1)[-1]
    if "/obo/CHMO_" in iri:
        return "CHMO:" + iri.rsplit("CHMO_", 1)[-1]
    if "/obo/OBI_" in iri:
        return "OBI:" + iri.rsplit("OBI_", 1)[-1]
    if "bioassayontology.org/bao#BAO_" in iri:
        return "BAO:" + iri.rsplit("BAO_", 1)[-1]
    if "/efo/EFO_" in iri:
        return "EFO:" + iri.rsplit("EFO_", 1)[-1]
    if "edamontology.org/topic_" in iri:
        return "EDAMT:" + iri.rsplit("topic_", 1)[-1]
    if "/obo/NCIT_" in iri:
        return "NCIT:" + iri.rsplit("NCIT_", 1)[-1]
    if "Thesaurus.owl#C" in iri:
        return "NCIT:" + iri.rsplit("#", 1)[-1]
    return iri


def base_doc(local_key, iri, label, synonyms, definition, parents, is_obsolete, ontology_name, source_name):
    return {
        "_id": iri,
        "iri": iri,
        "curie": curie_from_iri(iri),
        "label": label,
        "synonyms": synonyms,
        "definition": definition,
        "parents": parents,
        "ontology": ontology_name,
        "source": source_name,
        "is_obsolete": is_obsolete,
        "ontologies": [ontology_name],
        "source_ids": {local_key: iri},
        "ontology_terms": {
            local_key: {
                "iri": iri,
                "curie": curie_from_iri(iri),
                "label": label,
                "synonyms": synonyms,
                "definition": definition,
                "parents": parents,
                "is_obsolete": is_obsolete,
            }
        },
    }


def remapped_doc(local_key, local_iri, canonical_iri, label, synonyms, definition, parents, is_obsolete):
    canonical_onto = onto_from_iri(canonical_iri)
    onto_label = "EDAMT" if local_key == "edamt" else local_key.upper()
    return {
        "_id": canonical_iri,
        "ontology_terms": {
            local_key: {
                "iri": local_iri,
                "curie": curie_from_iri(local_iri),
                "label": label,
                "synonyms": synonyms,
                "definition": definition,
                "parents": parents,
                "is_obsolete": is_obsolete,
            }
        },
        "source_ids": {local_key: local_iri},
        "mapped_canonical_id": canonical_iri,
        "equivalent_ids": [canonical_iri, local_iri],
        "ontologies": sorted({canonical_onto, onto_label}),
    }
