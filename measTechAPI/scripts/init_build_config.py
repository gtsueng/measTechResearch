"""Create/update merged build configuration across all ontology plugins."""

import biothings.hub  # noqa: F401
from biothings.utils.hub_db import get_src_build_config


def main():
    col = get_src_build_config()
    conf = {
        "_id": "meastech_all_ontologies",
        "name": "meastech_all_ontologies",
        "doc_type": "measurement_technique",
        # Lowest->highest priority so highest overwrites top-level canonical fields.
        "sources": ["ncit", "edamt", "efo", "bao", "obi", "chmo", "mmo"],
        "root": ["ncit", "edamt", "efo", "bao", "obi", "chmo", "mmo"],
        "builder_class": "biothings.hub.databuild.builder.DataBuilder",
    }
    col.save(conf)
    print("Saved build config: meastech_all_ontologies")


if __name__ == "__main__":
    main()
