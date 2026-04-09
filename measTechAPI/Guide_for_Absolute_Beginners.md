# Guide for Absolute Beginners

This guide is for someone who wants to:

- set up `measTechAPI`
- update the ontology terms and mappings
- run the local BioThings hub

It assumes you are using this repository on Windows and that you will create a dedicated `measTechAPI` virtual environment at:

`measTechAPI/.venv`

## What This Project Does

`measTechAPI` builds a searchable API for measurement technique terms.

It combines terms from several ontologies:

- MMO
- CHMO
- OBI
- BAO
- EFO
- EDAMT
- NCIT

It also merges terms that are considered equivalent based on:

- BioPortal mappings
- manually curated mappings in this repository
- previously reviewed network-based mappings in this repository

Important:

- MMO is used as the highest-priority ontology when equivalent terms are merged.
- The other ontologies are filtered so only the measurement-technique branches are kept.

## Before You Start

You need:

1. This repository on your computer.
2. A base Python environment you can use to create `.venv`.
3. Internet access for refreshing ontology terms from BioPortal.
4. An NCBO BioPortal API key if you want to download the latest ontology data and mappings.
5. Docker Desktop or another working Docker installation if you want to run Elasticsearch locally.

Important:

- `requirements.txt` does not create the virtual environment by itself.
- First you create `.venv`.
- Then you activate `.venv`.
- Then you install the packages from `requirements.txt` into that environment.

## Folder You Will Use

Most commands in this guide should be run inside:

`measTechAPI`

You will create a local `.venv` inside `measTechAPI` during the setup steps below.

## Local Files You Must Create Yourself

Some files needed for local use are not stored in GitHub because they are ignored by `.gitignore`.

The most important ones are:

- `.venv`
- `secret_config.local.txt`
- `bin/ssh_host_key` and related SSH key files

This guide includes the steps to create them.

## Step 1: Open PowerShell

Open Windows PowerShell.

Then move into the `measTechAPI` folder:

```powershell
cd measTechAPI
```

## Step 2: Create the Project Environment

The `.venv` folder is local to your machine and is not stored in GitHub.

This matches the intended setup pattern used for this project:

1. create `.venv`
2. activate `.venv`
3. install `requirements.txt`

Run:

```powershell
python -m venv .venv
```

This may take a minute.

After that, you should have a new folder named `.venv` inside `measTechAPI`.

## Step 3: Activate the Project Environment

Run:

```powershell
.venv/Scripts/Activate.ps1
```

After that, your PowerShell prompt will usually start with `(.venv)`.

If PowerShell says script execution is blocked, run this once in the same window:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then try activating `.venv` again.

## Step 4: Check That Python Works

Run:

```powershell
python --version
```

If that prints a Python version, you are ready for the next step.

## Step 5: Install Python Packages

Run:

```powershell
python -m pip install -r requirements.txt
```

You only need to do this again if packages change.

This step installs the project packages into `.venv`. It does not create `.venv`.

## Step 6: Create `secret_config.local.txt`

This file is not included in the repository because it is ignored by Git.

Create it in the `measTechAPI` folder.

The file should be created at:

`measTechAPI/secret_config.local.txt`

The simplest way is to open Notepad and save a new file with that exact name.

Put this starter content into the file:

```text
# Local secret config for measTechAPI
# This file is ignored by Git and stays only on your machine.

# Required if you want to refresh ontology downloads and BioPortal mappings:
NCBO_API_KEY='your-real-api-key-here'

# Optional local BioThings hub guest login:
HUB_GUEST_PASSWORD='choose-a-local-password'
```

Save the file.

## Step 7: Set Your Local Secrets

`measTechAPI/secret_config.local.txt`

This file is for local-only settings and should not be committed.

At minimum, if you want to refresh ontology downloads from BioPortal, add your NCBO API key like this:

```text
NCBO_API_KEY='your-real-api-key-here'
```

You may also keep the hub guest login settings in the same file.

## Step 8: Refresh All Ontology Data

This is the step that updates the ontology term files and mappings used by the API.

Run:

```powershell
python scripts\refresh_all_sources.py --download-latest --refresh-mappings
```

What this does:

- downloads the latest ontology CSV files from BioPortal
- refreshes BioPortal mappings
- combines them with curated mappings already stored in this repository
- preserves the ontology priority hierarchy
- filters non-MMO ontologies down to the approved measurement-technique branches
- stages the final source files into the BioThings `data_archive`

If you do not want to download new ontology files and only want to reuse the local files already in the repository, run:

```powershell
python scripts\refresh_all_sources.py
```

## Step 9: Create the BioThings Build Configuration

Run:

```powershell
python scripts\init_build_config.py
```

This prepares the merged build configuration used by the BioThings hub.

## Step 10: Start Elasticsearch

The BioThings build process expects Elasticsearch.

If your local Docker setup already contains an Elasticsearch service, start it first.

Example:

```powershell
curl http://localhost:9200
```

If you get a response from Elasticsearch, that part is ready.

If you do not already have Elasticsearch running, you will need to start it using your local Docker setup before continuing.

## Step 11: Create the Hub SSH Key

The BioThings hub expects a local SSH host key.

This key is also not stored in GitHub because it is ignored by Git.

Run:

```powershell
mkdir bin
ssh-keygen -t rsa -b 4096 -N "" -f bin/ssh_host_key
```

If PowerShell says the `bin` folder already exists, that is fine.

After this step, you should have files such as:

- `bin/ssh_host_key`
- `bin/ssh_host_key.pub`

## Step 12: Start the BioThings Hub

Run:

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
python hub.py
```

Leave that window open.

## Step 13: Upload the Sources and Merge Them

Once the hub is running, use the BioThings hub shell to run:

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

This loads each source and then creates the merged measurement-technique build.

## Step 14: What Gets Updated

After a refresh, the main updated files are:

- `measTechNet/raw_files/*.csv`
- `measTechNet/results/ordered_mapping_best_dict.json`
- `measTechNet/results/bioportal_curated_mappings.tsv`
- `measTechAPI/data_archive/*/current/*`

## If You Only Want to Refresh One Ontology

Examples:

```powershell
python scripts\stage_efo_data.py --download-latest
python scripts\stage_chmo_data.py
```

If you want to refresh the shared mappings while doing that:

```powershell
python scripts\stage_chmo_data.py --refresh-mappings
```

## Common Problems

### Problem: `NCBO_API_KEY is required`

Cause:

- You asked the script to download latest ontology files or refresh mappings, but the API key is missing.

Fix:

- Add `NCBO_API_KEY='your-key'` to `secret_config.local.txt`
- or set it in PowerShell before running the script

Example:

```powershell
$env:NCBO_API_KEY = "your-real-api-key-here"
```

### Problem: `Source file not found`

Cause:

- A required ontology file was not downloaded and is not present locally.

Fix:

- Run the full refresh again with `--download-latest`

### Problem: Elasticsearch is not available

Cause:

- The hub cannot build or index data without Elasticsearch.

Fix:

- Start your local Elasticsearch service
- then retry `hub.py`

### Problem: `secret_config.local.txt` is missing

Cause:

- The file is ignored by Git, so it is not downloaded with the repository.

Fix:

- Create the file yourself
- add at least `NCBO_API_KEY='your-real-api-key-here'`
- add `HUB_GUEST_PASSWORD='choose-a-local-password'` if you want local guest login

### Problem: `bin/ssh_host_key` is missing

Cause:

- The SSH host key is ignored by Git, so it must be generated locally.

Fix:

- Run:

```powershell
mkdir bin
ssh-keygen -t rsa -b 4096 -N "" -f bin/ssh_host_key
```

### Problem: The hub starts but you do not see a prompt

Cause:

- Some local setups start the services without dropping directly into an interactive prompt.

Fix:

- Keep the hub process running
- then connect using the workflow already described in `secret_config.local.txt` if needed

## The Safest Routine for Updating Everything

If you just want one short checklist, use this order:

1. Open PowerShell.
2. Go to `measTechAPI`.
3. Create `.venv` if it does not already exist.
4. Activate `.venv`.
5. Create `secret_config.local.txt` if it does not already exist.
6. Generate `bin/ssh_host_key` if it does not already exist.
7. Make sure `NCBO_API_KEY` is set in `secret_config.local.txt`.
8. Run:

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
python scripts\refresh_all_sources.py --download-latest --refresh-mappings
python scripts\init_build_config.py
mkdir bin
ssh-keygen -t rsa -b 4096 -N "" -f bin/ssh_host_key
```

9. Start Elasticsearch.
10. Start `hub.py`.
11. Upload each source.
12. Run `merge('meastech_all_ontologies')`.

## Files You May Want to Read Later

- `measTechAPI/README.md`
- `measTechAPI/secret_config.local.txt`
- `measTechAPI/scripts/source_refresh.py`
- `measTechAPI/scripts/refresh_all_sources.py`

## Final Note

If you are unsure, the single most important update command is:

```powershell
python scripts\refresh_all_sources.py --download-latest --refresh-mappings
```

That is the command that updates the ontology source files and mappings used by `measTechAPI`.
