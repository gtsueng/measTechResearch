"""Parse CHMO CSV rows into BioThings documents."""

import csv
import json
from pathlib import Path


def _split_pipe(value):
    if not value:
        return []
    return [part.strip() for part in value.split("|") if part.strip()]


def _curie_from_iri(iri):
    if "/obo/CHMO_" in iri:
        return "CHMO:" + iri.rsplit("CHMO_", 1)[-1]
    if "/obo/MMO_" in iri:
        return "MMO:" + iri.rsplit("MMO_", 1)[-1]
    if "/obo/OBI_" in iri:
        return "OBI:" + iri.rsplit("OBI_", 1)[-1]
    return iri


def _load_chmo_map(data_folder):
    mapping_path = Path(data_folder) / "chmo_to_canonical_map.json"
    if not mapping_path.exists():
        return {}
    data = json.loads(mapping_path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _ontology_from_iri(iri):
    if "/obo/MMO_" in iri:
        return "MMO"
    if "/obo/CHMO_" in iri:
        return "CHMO"
    if "/obo/OBI_" in iri:
        return "OBI"
    return "UNKNOWN"


def _doc_from_row(row, chmo_map):
    chmo_iri = (row.get("Class ID") or "").strip()
    if not chmo_iri:
        return None

    canonical_iri = chmo_map.get(chmo_iri, chmo_iri)
    canonical_onto = _ontology_from_iri(canonical_iri)
    label = (row.get("Preferred Label") or "").strip()
    synonyms = _split_pipe((row.get("Synonyms") or "").strip())
    definition = (row.get("Definitions") or row.get("definition") or "").strip()
    parents = _split_pipe((row.get("Parents") or "").strip())
    is_obsolete = str(row.get("Obsolete", "")).lower() == "true"

    doc = {
        "_id": canonical_iri,
        "ontology_terms": {
            "chmo": {
                "iri": chmo_iri,
                "curie": _curie_from_iri(chmo_iri),
                "label": label,
                "synonyms": synonyms,
                "definition": definition,
                "parents": parents,
                "is_obsolete": is_obsolete,
            }
        },
        "source_ids": {"chmo": chmo_iri},
    }

    if canonical_iri != chmo_iri:
        doc["mapped_canonical_id"] = canonical_iri
        doc["equivalent_ids"] = [canonical_iri, chmo_iri]
        doc["ontologies"] = sorted({"CHMO", canonical_onto})
    else:
        doc.update(
            {
                "iri": chmo_iri,
                "curie": _curie_from_iri(chmo_iri),
                "label": label,
                "synonyms": synonyms,
                "definition": definition,
                "parents": parents,
                "ontology": "CHMO",
                "source": "Chemical Methods Ontology",
                "is_obsolete": is_obsolete,
                "ontologies": ["CHMO"],
            }
        )

    return doc


def load_data(data_folder):
    data_path = Path(data_folder)
    csv_path = data_path / "CHMO.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"CHMO source not found: {csv_path}")

    chmo_map = _load_chmo_map(data_path)

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            doc = _doc_from_row(row, chmo_map)
            if doc:
                yield doc
