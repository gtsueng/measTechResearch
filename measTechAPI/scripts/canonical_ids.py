"""Build canonical ID maps across ontology IDs with fixed priority order.

Priority order used for canonical _id assignment:
MMO > CHMO > OBI > BAO > EFO > EDAMT > NCIT
"""

from collections import defaultdict

PRIORITY = ("MMO", "CHMO", "OBI", "BAO", "EFO", "EDAMT", "NCIT")


def _ontology(iri):
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


def _is_supported_pair(left, right):
    return _ontology(left) in PRIORITY and _ontology(right) in PRIORITY


def _build_components(edges):
    graph = defaultdict(set)
    nodes = set()
    for left, right in edges:
        if left == right:
            nodes.add(left)
            continue
        graph[left].add(right)
        graph[right].add(left)
        nodes.add(left)
        nodes.add(right)

    seen = set()
    components = []
    for node in nodes:
        if node in seen:
            continue
        stack = [node]
        comp = set()
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            comp.add(cur)
            stack.extend(graph[cur] - seen)
        components.append(comp)
    return components


def _pick_canonical(component):
    by_onto = defaultdict(list)
    for iri in component:
        by_onto[_ontology(iri)].append(iri)

    for onto in PRIORITY:
        if by_onto.get(onto):
            return sorted(by_onto[onto])[0]
    return sorted(component)[0]


def build_canonical_maps(mapping_dict):
    edges = [(left, right) for left, right in mapping_dict.items() if _is_supported_pair(left, right)]
    components = _build_components(edges)

    canonical_by_id = {}
    for comp in components:
        canonical = _pick_canonical(comp)
        for iri in comp:
            canonical_by_id[iri] = canonical

    by_onto = {onto: {} for onto in PRIORITY}
    for iri, canonical in canonical_by_id.items():
        onto = _ontology(iri)
        if onto and iri != canonical:
            by_onto[onto][iri] = canonical

    stats = {
        "edges_considered": len(edges),
        "components": len(components),
    }
    for onto in PRIORITY:
        stats[f"{onto.lower()}_links"] = len(by_onto[onto])

    return by_onto, stats


def build_canonical_map_for(mapping_dict, ontology_name):
    by_onto, stats = build_canonical_maps(mapping_dict)
    return by_onto.get(ontology_name, {}), stats
