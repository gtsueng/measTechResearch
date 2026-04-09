# measTechAPI (BioThings SDK starter)

This folder contains a BioThings SDK starter runtime for a measurement-technique API.
The merged source set is MMO + CHMO + OBI + BAO + EFO + EDAMT + NCIT.

Canonical `_id` priority for synonym groups:

1. MMO
2. CHMO
3. OBI
4. BAO
5. EFO
6. EDAMT
7. NCIT

## Document Summary

<!-- DOC_SUMMARY_START -->
- Total documents: `255,046`
- Unique documents (one ontology only): `254,133`
- Merged documents (more than one ontology): `913`

Merged document size distribution:
- 2 ontologies: `808`
- 3 ontologies: `95`
- 4 ontologies: `8`
- 5 ontologies: `2`
<!-- DOC_SUMMARY_END -->

## Stage source data

```powershell
cd measTechAPI
python scripts\refresh_all_sources.py
```

That uses the repo-local staged CSVs already present in `measTechNet/raw_files` and the current curated mapping artifacts.

## Pull latest ontology terms and mappings

Set an NCBO BioPortal API key in `secret_config.local.txt` or your shell environment:

```powershell
$env:NCBO_API_KEY = "your-ncbo-key"
```

Then refresh the ontology CSVs from BioPortal and rebuild canonical mappings from:

- BioPortal ontology mappings
- curated mapping TSVs in `measTechAnalysis/result/mappings`
- curated network mappings in `measTechNet/results/results_from_cytoscape/mappings_found_via_network.json`
- previously curated measurement-technique branch roots in `measTechNet/results/parent_inclusion_list.txt`
- previously curated exclusions in `measTechNet/results/delete_list.txt`

```powershell
cd measTechAPI
python scripts\refresh_all_sources.py --download-latest --refresh-mappings
```

This writes refreshed ontology CSVs back to `measTechNet/raw_files`, rewrites `measTechNet/results/ordered_mapping_best_dict.json`, exports the combined mapping table to `measTechNet/results/bioportal_curated_mappings.tsv`, and stages the current BioThings source files into `data_archive/*/current`.

During staging, all non-MMO ontologies are filtered down to descendants of the previously curated branch roots before they are copied into `data_archive`. MMO is kept whole because it is already measurement-technique focused.

If you want to refresh just one ontology source, the per-source scripts now support the same flags, for example:

```powershell
python scripts\stage_efo_data.py --download-latest
python scripts\stage_chmo_data.py --refresh-mappings
```

## Build config

```powershell
cd measTechAPI
python scripts\init_build_config.py
```

This creates build config `meastech_all_ontologies` with source order:

- `ncit`, `edamt`, `efo`, `bao`, `obi`, `chmo`, `mmo`

That order preserves MMO as canonical top-level values on overlapping terms.

## Run hub

```powershell
cd measTechAPI
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
python hub.py
```

Then in hub shell:

```python
upload('ncit')
upload('edamt')
upload('efo')
upload('bao')
upload('obi')
upload('chmo')
upload('mmo')
merge('meastech_all_ontologies')
```
