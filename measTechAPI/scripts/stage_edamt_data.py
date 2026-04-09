"""Stage EDAM topic source data into DATA_ARCHIVE_ROOT/edamt/current."""

import argparse
import json

from source_refresh import stage_ontology


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-latest", action="store_true", help="Download the latest EDAM CSV from BioPortal first.")
    parser.add_argument("--refresh-mappings", action="store_true", help="Refresh BioPortal and curated canonical mappings.")
    args = parser.parse_args()

    result = stage_ontology(
        "EDAMT",
        use_bioportal_downloads=args.download_latest,
        refresh_mappings=args.refresh_mappings,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
