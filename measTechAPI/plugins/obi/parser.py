"""Parse OBI CSV rows into BioThings documents."""

import csv
import json
from pathlib import Path


def _split_pipe(value):
    if not value:
        return []
    return [part.strip() for part in value.split("|") if part.strip()]


def _curie_from_iri(iri):
    if "/obo/OBI_" in iri:
        return "OBI:" + iri.rsplit("OBI_", 1)[-1]
    if "/obo/MMO_" in iri:
        return "MMO:" + iri.rsplit("MMO_", 1)[-1]
    if "/obo/CHMO_" in iri:
        return "CHMO:" + iri.rsplit("CHMO_", 1)[-1]
    return iri


def _load_obi_map(data_folder):
    mapping_path = Path(data_folder) / "obi_to_canonical_map.json"
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


def _doc_from_row(row, obi_map):
    obi_iri = (row.get("Class ID") or "").strip()
    if not obi_iri:
        return None

    canonical_iri = obi_map.get(obi_iri, obi_iri)
    canonical_onto = _ontology_from_iri(canonical_iri)

    label = (row.get("Preferred Label") or row.get("label") or "").strip()
    synonyms = _split_pipe((row.get("Synonyms") or row.get("alternative term") or "").strip())
    definition = (row.get("Definitions") or row.get("definition") or row.get("textual definition") or "").strip()
    parents = _split_pipe((row.get("Parents") or row.get("part of") or "").strip())
    is_obsolete = str(row.get("Obsolete", "")).lower() == "true"

    doc = {
        "_id": canonical_iri,
        "ontology_terms": {
            "obi": {
                "iri": obi_iri,
                "curie": _curie_from_iri(obi_iri),
                "label": label,
                "synonyms": synonyms,
                "definition": definition,
                "parents": parents,
                "is_obsolete": is_obsolete,
            }
        },
        "source_ids": {"obi": obi_iri},
    }

    if canonical_iri != obi_iri:
        doc["mapped_canonical_id"] = canonical_iri
        doc["equivalent_ids"] = [canonical_iri, obi_iri]
        doc["ontologies"] = sorted({"OBI", canonical_onto})
    else:
        doc.update(
            {
                "iri": obi_iri,
                "curie": _curie_from_iri(obi_iri),
                "label": label,
                "synonyms": synonyms,
                "definition": definition,
                "parents": parents,
                "ontology": "OBI",
                "source": "Ontology for Biomedical Investigations",
                "is_obsolete": is_obsolete,
                "ontologies": ["OBI"],
            }
        )

    return doc


def load_data(data_folder):
    data_path = Path(data_folder)
    csv_path = data_path / "OBI.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"OBI source not found: {csv_path}")

    obi_map = _load_obi_map(data_path)

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            doc = _doc_from_row(row, obi_map)
            if doc:
                yield doc
