"""Refresh ontology source CSVs and canonical mappings for measTechAPI."""

from __future__ import annotations

import csv
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple

import requests

from canonical_ids import PRIORITY, build_canonical_map_for

BIOPORTAL_API_BASE = "https://data.bioontology.org"
REQUEST_TIMEOUT = 120
DEFAULT_PAGE_SIZE = 500
SUPPORTED_ONTOLOGIES = ("MMO", "CHMO", "OBI", "BAO", "EFO", "EDAMT", "NCIT")
BIOPORTAL_ACRONYMS = {
    "MMO": "MMO",
    "CHMO": "CHMO",
    "OBI": "OBI",
    "BAO": "BAO",
    "EFO": "EFO",
    "EDAMT": "EDAM",
    "NCIT": "NCIT",
}
@dataclass(frozen=True)
class OntologySource:
    ontology_name: str
    plugin_name: str
    source_file_name: str
    bioportal_acronym: str
    archive_file_name: str
    mapping_file_name: Optional[str]


ONTOLOGY_SOURCES: Dict[str, OntologySource] = {
    "MMO": OntologySource("MMO", "mmo", "MMO.csv", "MMO", "MMO.csv", None),
    "CHMO": OntologySource("CHMO", "chmo", "CHMO.csv", "CHMO", "CHMO.csv", "chmo_to_canonical_map.json"),
    "OBI": OntologySource("OBI", "obi", "OBI.csv", "OBI", "OBI.csv", "obi_to_canonical_map.json"),
    "BAO": OntologySource("BAO", "bao", "BAO.csv", "BAO", "BAO.csv", "bao_to_canonical_map.json"),
    "EFO": OntologySource("EFO", "efo", "EFO.csv", "EFO", "EFO.csv", "efo_to_canonical_map.json"),
    "EDAMT": OntologySource("EDAMT", "edamt", "EDAMT.csv", "EDAM", "EDAMT.csv", "edamt_to_canonical_map.json"),
    "NCIT": OntologySource("NCIT", "ncit", "NCIT.csv", "NCIT", "NCIT.csv", "ncit_to_canonical_map.json"),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def api_root() -> Path:
    return Path(__file__).resolve().parents[1]


def raw_files_dir() -> Path:
    return repo_root() / "measTechNet" / "raw_files"


def curated_mapping_dir() -> Path:
    return repo_root() / "measTechAnalysis" / "result" / "mappings"


def net_results_dir() -> Path:
    return repo_root() / "measTechNet" / "results"


def archive_current_dir(plugin_name: str) -> Path:
    return api_root() / "data_archive" / plugin_name / "current"


def load_local_secret_settings() -> Dict[str, str]:
    settings: Dict[str, str] = {}
    secret_path = api_root() / "secret_config.local.txt"
    if not secret_path.exists():
        return settings
    for raw_line in secret_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        settings[key.strip()] = value.strip().strip("'").strip('"')
    return settings


def get_ncbo_api_key() -> Optional[str]:
    return os.environ.get("NCBO_API_KEY") or load_local_secret_settings().get("NCBO_API_KEY")


def split_pipe(value: str) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split("|") if part.strip()]


def canonicalize_iri(iri: str) -> str:
    value = iri.strip()
    if not value:
        return value
    if value.startswith("http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C"):
        return value.replace(
            "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#",
            "http://purl.obolibrary.org/obo/NCIT_",
        )
    if value.startswith("http://purl.obofoundry.org/obo/"):
        return value.replace("http://purl.obofoundry.org/obo/", "http://purl.obolibrary.org/obo/")
    if value.startswith("http://uri.neuinfo.org/nif/nifstd/OBI_"):
        return value.replace("http://uri.neuinfo.org/nif/nifstd/OBI_", "http://purl.obolibrary.org/obo/OBI_")
    return value


def build_session(api_key: Optional[str] = None) -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    if api_key:
        session.headers["Authorization"] = f"apikey token={api_key}"
    return session


def _request_json(session: requests.Session, url: str, params: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object from {response.url}, got {type(payload).__name__}")
    return payload


def download_latest_ontology_csv(source: OntologySource, session: requests.Session, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    url = f"{BIOPORTAL_API_BASE}/ontologies/{source.bioportal_acronym}/download"
    params = {"download_format": "csv"}
    response = session.get(url, params=params, timeout=REQUEST_TIMEOUT, stream=True)
    response.raise_for_status()
    with destination.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                handle.write(chunk)
    return destination


def _collection_items(payload: Dict[str, object]) -> List[Dict[str, object]]:
    collection = payload.get("collection")
    if isinstance(collection, list):
        return [item for item in collection if isinstance(item, dict)]
    return []


def iter_paginated_collection(
    session: requests.Session, url: str, params: Optional[Dict[str, object]] = None
) -> Iterator[Dict[str, object]]:
    next_url = url
    next_params = dict(params or {})
    while next_url:
        payload = _request_json(session, next_url, next_params)
        for item in _collection_items(payload):
            yield item
        links = payload.get("links")
        next_link = None
        if isinstance(links, dict):
            raw_next = links.get("nextPage")
            if isinstance(raw_next, str) and raw_next:
                next_link = raw_next
        next_url = next_link
        next_params = None


def _mapping_classes(mapping_record: Dict[str, object]) -> List[Dict[str, object]]:
    classes = mapping_record.get("classes")
    if isinstance(classes, list):
        return [item for item in classes if isinstance(item, dict)]
    return []


def _mapping_process(mapping_record: Dict[str, object]) -> str:
    process = mapping_record.get("process")
    if isinstance(process, list):
        values = [value for value in process if isinstance(value, str) and value]
        return "|".join(values)
    if isinstance(process, str):
        return process
    return ""


def fetch_bioportal_mappings(
    session: requests.Session, ontology_name: str, target_ontologies: Optional[Sequence[str]] = None
) -> List[Dict[str, str]]:
    source = ONTOLOGY_SOURCES[ontology_name]
    allowed_targets = set(target_ontologies or SUPPORTED_ONTOLOGIES)
    records: List[Dict[str, str]] = []
    url = f"{BIOPORTAL_API_BASE}/ontologies/{source.bioportal_acronym}/mappings"
    params = {"pagesize": DEFAULT_PAGE_SIZE}
    for mapping in iter_paginated_collection(session, url, params):
        classes = _mapping_classes(mapping)
        if len(classes) < 2:
            continue
        class_pairs = []
        for entry in classes:
            links = entry.get("links")
            ontology_link = None
            if isinstance(links, dict):
                ontology_link = links.get("ontology")
            class_id = entry.get("@id") or entry.get("id")
            if not isinstance(class_id, str) or not class_id:
                continue
            ontology_name_for_class = ontology_name_from_bioportal_link(ontology_link)
            if ontology_name_for_class not in SUPPORTED_ONTOLOGIES:
                ontology_name_for_class = ontology_name_from_iri(class_id)
            class_pairs.append((ontology_name_for_class, class_id))
        for idx, (left_ontology, left_id) in enumerate(class_pairs):
            if left_ontology != ontology_name:
                continue
            for right_ontology, right_id in class_pairs[idx + 1 :]:
                if right_ontology not in allowed_targets or right_ontology == ontology_name:
                    continue
                records.append(
                    {
                        "source_ontology": ontology_name,
                        "source_id": left_id,
                        "target_ontology": right_ontology,
                        "target_id": right_id,
                        "map_method": _mapping_process(mapping) or "BIOPORTAL",
                    }
                )
    return records


def ontology_name_from_bioportal_link(link: object) -> Optional[str]:
    if not isinstance(link, str):
        return None
    suffix = link.rstrip("/").rsplit("/", 1)[-1]
    for ontology_name, acronym in BIOPORTAL_ACRONYMS.items():
        if suffix == acronym:
            return ontology_name
    return None


def ontology_name_from_iri(iri: str) -> Optional[str]:
    iri = canonicalize_iri(iri)
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
    return None


def _load_tsv_mapping_rows(path: Path) -> Iterator[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            cleaned = {str(key).strip(): (value or "").strip() for key, value in row.items() if key}
            if cleaned:
                yield cleaned


def load_curated_mapping_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for ontology_name in SUPPORTED_ONTOLOGIES:
        path = curated_mapping_dir() / f"{ontology_name if ontology_name != 'EDAMT' else 'EDAM'}_mappings.tsv"
        if not path.exists():
            continue
        for row in _load_tsv_mapping_rows(path):
            source_id = row.get("source_id", "")
            target_id = row.get("target_id", "")
            source_ontology = ontology_name_from_iri(source_id) or row.get("source_ontology") or ontology_name
            target_ontology = ontology_name_from_iri(target_id)
            if (
                source_ontology in SUPPORTED_ONTOLOGIES
                and target_ontology in SUPPORTED_ONTOLOGIES
                and source_id
                and target_id
                and source_ontology != target_ontology
            ):
                rows.append(
                    {
                        "source_ontology": source_ontology,
                        "source_id": source_id,
                        "target_ontology": target_ontology,
                        "target_id": target_id,
                        "map_method": row.get("map_method", "") or "CURATED_TSV",
                    }
                )
    return rows


def load_branch_root_ids() -> Dict[str, Set[str]]:
    path = net_results_dir() / "parent_inclusion_list.txt"
    branch_roots: Dict[str, Set[str]] = {ontology_name: set() for ontology_name in SUPPORTED_ONTOLOGIES}
    if not path.exists():
        return branch_roots
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        iri = canonicalize_iri(raw_line.strip())
        if not iri:
            continue
        ontology_name = ontology_name_from_iri(iri)
        if ontology_name in branch_roots:
            branch_roots[ontology_name].add(iri)
    return branch_roots


def load_delete_ids() -> Set[str]:
    path = net_results_dir() / "delete_list.txt"
    if not path.exists():
        return set()
    return {canonicalize_iri(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _row_parent_ids(row: Dict[str, str]) -> List[str]:
    parents = row.get("Parents") or row.get("part of") or row.get("part_of") or ""
    return [canonicalize_iri(parent) for parent in split_pipe(parents)]


def filter_csv_to_branch_terms(source_csv: Path, ontology_name: str, destination_csv: Path) -> Dict[str, object]:
    destination_csv.parent.mkdir(parents=True, exist_ok=True)
    if ontology_name == "MMO":
        shutil.copy2(source_csv, destination_csv)
        return {"kept_rows": None, "input_rows": None, "branch_roots": "ALL"}

    branch_roots = load_branch_root_ids().get(ontology_name, set())
    if not branch_roots:
        raise RuntimeError(f"No branch roots found for {ontology_name} in parent_inclusion_list.txt")

    delete_ids = load_delete_ids()
    with source_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise ValueError(f"CSV has no header: {source_csv}")
        rows = list(reader)

    id_to_row: Dict[str, Dict[str, str]] = {}
    child_to_parents: Dict[str, Set[str]] = {}
    for row in rows:
        raw_id = (row.get("Class ID") or "").strip()
        if not raw_id:
            continue
        class_id = canonicalize_iri(raw_id)
        row["Class ID"] = class_id
        normalized_parents = _row_parent_ids(row)
        if normalized_parents:
            row["Parents"] = "|".join(normalized_parents)
        id_to_row[class_id] = row
        child_to_parents[class_id] = set(normalized_parents)

    keep_ids = set(branch_roots)
    frontier = list(branch_roots)
    while frontier:
        current_parent = frontier.pop()
        for child_id, parent_ids in child_to_parents.items():
            if child_id in keep_ids:
                continue
            if current_parent in parent_ids:
                keep_ids.add(child_id)
                frontier.append(child_id)

    keep_ids.difference_update(delete_ids)
    filtered_rows = [id_to_row[class_id] for class_id in id_to_row if class_id in keep_ids]

    with destination_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_rows)

    return {
        "input_rows": len(rows),
        "kept_rows": len(filtered_rows),
        "branch_roots": len(branch_roots),
        "deleted_ids": len(delete_ids.intersection(set(id_to_row))),
    }


def load_network_curated_mapping_rows() -> List[Dict[str, str]]:
    path = net_results_dir() / "results_from_cytoscape" / "mappings_found_via_network.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return []
    rows: List[Dict[str, str]] = []
    for source_id, target_id in payload.items():
        if not isinstance(source_id, str) or not isinstance(target_id, str):
            continue
        source_ontology = ontology_name_from_iri(source_id)
        target_ontology = ontology_name_from_iri(target_id)
        if (
            source_ontology in SUPPORTED_ONTOLOGIES
            and target_ontology in SUPPORTED_ONTOLOGIES
            and source_ontology != target_ontology
        ):
            rows.append(
                {
                    "source_ontology": source_ontology,
                    "source_id": source_id,
                    "target_ontology": target_ontology,
                    "target_id": target_id,
                    "map_method": "CURATED_NETWORK",
                }
            )
    return rows


def dedupe_mapping_rows(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    seen: Set[Tuple[str, str, str, str]] = set()
    deduped: List[Dict[str, str]] = []
    for row in rows:
        source_ontology = row["source_ontology"]
        source_id = row["source_id"]
        target_ontology = row["target_ontology"]
        target_id = row["target_id"]
        key = (source_ontology, source_id, target_ontology, target_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def build_mapping_dict(rows: Iterable[Dict[str, str]]) -> Dict[str, str]:
    priority_index = {name: idx for idx, name in enumerate(PRIORITY)}
    pair_rows: Dict[frozenset[str], Dict[str, str]] = {}
    for row in rows:
        source_id = row["source_id"]
        target_id = row["target_id"]
        if source_id == target_id:
            continue
        source_ontology = row["source_ontology"]
        target_ontology = row["target_ontology"]
        if source_ontology not in priority_index or target_ontology not in priority_index:
            continue
        pair_key = frozenset((source_id, target_id))
        current = pair_rows.get(pair_key)
        candidate = row
        if current is None or priority_index[source_ontology] < priority_index[current["source_ontology"]]:
            pair_rows[pair_key] = candidate

    mapping_dict: Dict[str, str] = {}
    for row in pair_rows.values():
        mapping_dict[row["source_id"]] = row["target_id"]
    return mapping_dict


def refresh_mapping_artifacts(session: Optional[requests.Session] = None) -> Tuple[Dict[str, str], Dict[str, object]]:
    rows: List[Dict[str, str]] = []
    for ontology_name in SUPPORTED_ONTOLOGIES:
        if session is not None:
            rows.extend(fetch_bioportal_mappings(session, ontology_name, SUPPORTED_ONTOLOGIES))
    rows.extend(load_curated_mapping_rows())
    rows.extend(load_network_curated_mapping_rows())
    deduped_rows = dedupe_mapping_rows(rows)
    mapping_dict = build_mapping_dict(deduped_rows)

    results_dir = net_results_dir()
    results_dir.mkdir(parents=True, exist_ok=True)
    mapping_path = results_dir / "ordered_mapping_best_dict.json"
    mapping_path.write_text(json.dumps(mapping_dict, indent=2, sort_keys=True), encoding="utf-8")

    export_path = results_dir / "bioportal_curated_mappings.tsv"
    with export_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_ontology", "source_id", "target_ontology", "target_id", "map_method"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(deduped_rows)

    return mapping_dict, {"mapping_count": len(mapping_dict), "row_count": len(deduped_rows), "path": str(mapping_path)}


def stage_ontology(
    ontology_name: str,
    *,
    use_bioportal_downloads: bool = False,
    refresh_mappings: bool = False,
    api_key: Optional[str] = None,
) -> Dict[str, object]:
    source = ONTOLOGY_SOURCES[ontology_name]
    session = build_session(api_key) if use_bioportal_downloads or refresh_mappings else None
    src_path = raw_files_dir() / source.source_file_name

    if use_bioportal_downloads:
        src_path = download_latest_ontology_csv(source, session, src_path)  # type: ignore[arg-type]

    if not src_path.exists():
        raise FileNotFoundError(f"Source file not found: {src_path}")

    mapping_dict = None
    mapping_stats = None
    if source.mapping_file_name:
        if refresh_mappings:
            _, mapping_stats = refresh_mapping_artifacts(session)
        ordered_mapping_path = net_results_dir() / "ordered_mapping_best_dict.json"
        if not ordered_mapping_path.exists():
            raise FileNotFoundError(
                f"Canonical mapping source not found: {ordered_mapping_path}. "
                "Run with refresh_mappings enabled or provide the file."
            )
        raw_map = json.loads(ordered_mapping_path.read_text(encoding="utf-8"))
        mapping_dict, build_stats = build_canonical_map_for(raw_map, ontology_name)
        mapping_stats = mapping_stats or {}
        mapping_stats = {**mapping_stats, **build_stats, "ontology_links": len(mapping_dict)}

    dst_dir = archive_current_dir(source.plugin_name)
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst_csv = dst_dir / source.archive_file_name
    filter_stats = filter_csv_to_branch_terms(src_path, ontology_name, dst_csv)

    result: Dict[str, object] = {"csv_path": str(dst_csv), "source_csv": str(src_path), "filter_stats": filter_stats}
    if source.mapping_file_name and mapping_dict is not None:
        dst_map = dst_dir / source.mapping_file_name
        dst_map.write_text(json.dumps(mapping_dict, indent=2, sort_keys=True), encoding="utf-8")
        result["mapping_path"] = str(dst_map)
        result["mapping_stats"] = mapping_stats
    return result


def refresh_all_sources(*, use_bioportal_downloads: bool = False, refresh_mappings: bool = False) -> Dict[str, Dict[str, object]]:
    api_key = get_ncbo_api_key()
    if (use_bioportal_downloads or refresh_mappings) and not api_key:
        raise RuntimeError("NCBO_API_KEY is required for BioPortal downloads and mappings refresh.")

    if refresh_mappings:
        refresh_mapping_artifacts(build_session(api_key))

    results: Dict[str, Dict[str, object]] = {}
    for ontology_name in SUPPORTED_ONTOLOGIES:
        result = stage_ontology(
            ontology_name,
            use_bioportal_downloads=use_bioportal_downloads,
            refresh_mappings=False,
            api_key=api_key,
        )
        results[ontology_name] = result
    return results
