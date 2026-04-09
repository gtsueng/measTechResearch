"""Parse BAO CSV rows into BioThings documents."""

from pathlib import Path

from plugins._common import base_doc, load_map, read_rows, remapped_doc, split_pipe


def _doc_from_row(row, bao_map):
    iri = (row.get("Class ID") or "").strip()
    if not iri:
        return None
    canonical = bao_map.get(iri, iri)
    label = (row.get("Preferred Label") or row.get("label") or "").strip()
    synonyms = split_pipe((row.get("Synonyms") or row.get("alternative term") or "").strip())
    definition = (row.get("Definitions") or row.get("definition") or row.get("textual definition") or "").strip()
    parents = split_pipe((row.get("Parents") or row.get("part of") or "").strip())
    is_obsolete = str(row.get("Obsolete", "")).lower() == "true"

    if canonical != iri:
        return remapped_doc("bao", iri, canonical, label, synonyms, definition, parents, is_obsolete)
    return base_doc("bao", iri, label, synonyms, definition, parents, is_obsolete, "BAO", "BioAssay Ontology")


def load_data(data_folder):
    data_path = Path(data_folder)
    csv_path = data_path / "BAO.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"BAO source not found: {csv_path}")

    bao_map = load_map(data_path, "bao_to_canonical_map.json")
    for row in read_rows(csv_path):
        doc = _doc_from_row(row, bao_map)
        if doc:
            yield doc
