"""Parse MMO CSV rows into BioThings documents."""

import csv
from pathlib import Path


def _split_synonyms(value):
    if not value:
        return []
    return [s.strip() for s in value.split("|") if s.strip()]


def _curie_from_class_id(class_id):
    # Example: http://purl.obolibrary.org/obo/MMO_0000097 -> MMO:0000097
    if "/obo/MMO_" in class_id:
        return "MMO:" + class_id.rsplit("MMO_", 1)[-1]
    return class_id


def _doc_from_row(row):
    class_id = (row.get("Class ID") or "").strip()
    if not class_id:
        return None

    label = (row.get("Preferred Label") or "").strip()
    synonyms = _split_synonyms((row.get("Synonyms") or "").strip())
    definition = (row.get("Definitions") or row.get("definition") or "").strip()
    parents = _split_synonyms((row.get("Parents") or "").strip())
    curie = _curie_from_class_id(class_id)
    is_obsolete = str(row.get("Obsolete", "")).lower() == "true"

    doc = {
        "_id": class_id,
        "iri": class_id,
        "curie": curie,
        "label": label,
        "synonyms": synonyms,
        "definition": definition,
        "parents": parents,
        "ontology": "MMO",
        "source": "Measurement Method Ontology",
        "is_obsolete": is_obsolete,
        "ontologies": ["MMO"],
        "source_ids": {"mmo": class_id},
        "ontology_terms": {
            "mmo": {
                "iri": class_id,
                "curie": curie,
                "label": label,
                "synonyms": synonyms,
                "definition": definition,
                "parents": parents,
                "is_obsolete": is_obsolete,
            }
        },
    }

    return doc


def load_data(data_folder):
    """Yield BioThings documents from MMO.csv in a data folder."""
    data_path = Path(data_folder)
    csv_path = data_path / "MMO.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"MMO source not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            doc = _doc_from_row(row)
            if doc:
                yield doc
