"""Parse NCIT CSV rows into BioThings documents."""

from pathlib import Path

from plugins._common import base_doc, load_map, read_rows, remapped_doc, split_pipe


def _doc_from_row(row, ncit_map):
    iri = (row.get("Class ID") or "").strip()
    if not iri:
        return None
    canonical = ncit_map.get(iri, iri)
    label = (row.get("Preferred Label") or row.get("Preferred_Name") or "").strip()
    synonyms = split_pipe((row.get("Synonyms") or row.get("FULL_SYN") or "").strip())
    definition = (row.get("Definitions") or row.get("DEFINITION") or row.get("def-definition") or "").strip()
    parents = split_pipe((row.get("Parents") or "").strip())
    is_obsolete = str(row.get("Obsolete", "")).lower() == "true"

    if canonical != iri:
        return remapped_doc("ncit", iri, canonical, label, synonyms, definition, parents, is_obsolete)
    return base_doc("ncit", iri, label, synonyms, definition, parents, is_obsolete, "NCIT", "NCI Thesaurus")


def load_data(data_folder):
    data_path = Path(data_folder)
    csv_path = data_path / "NCIT.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"NCIT source not found: {csv_path}")

    ncit_map = load_map(data_path, "ncit_to_canonical_map.json")
    for row in read_rows(csv_path):
        doc = _doc_from_row(row, ncit_map)
        if doc:
            yield doc
