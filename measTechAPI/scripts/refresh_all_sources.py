"""Refresh all ontology CSVs and canonical mappings for measTechAPI."""

import argparse
import json

from source_refresh import refresh_all_sources


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-latest", action="store_true", help="Download the latest ontology CSVs from BioPortal.")
    parser.add_argument("--refresh-mappings", action="store_true", help="Refresh BioPortal and curated canonical mappings.")
    args = parser.parse_args()

    result = refresh_all_sources(
        use_bioportal_downloads=args.download_latest,
        refresh_mappings=args.refresh_mappings,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
