"""Stage MMO source data into DATA_ARCHIVE_ROOT/mmo/current."""

import argparse
import json

from source_refresh import stage_ontology


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-latest", action="store_true", help="Download the latest MMO CSV from BioPortal first.")
    args = parser.parse_args()

    result = stage_ontology("MMO", use_bioportal_downloads=args.download_latest)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
