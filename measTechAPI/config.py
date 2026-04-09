"""BioThings Hub config for measTech API starter."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOG_FOLDER = str(BASE_DIR / "logs")
DATA_ARCHIVE_ROOT = str(BASE_DIR / "data_archive")
DIFF_PATH = str(BASE_DIR / "diff")
RELEASE_PATH = str(BASE_DIR / "release")
DATA_PLUGIN_FOLDER = str(BASE_DIR / "plugins")

# Local default: SQLite Hub DB (no MongoDB service needed).
HUB_DB_BACKEND = {
    "module": "biothings.utils.sqlite3",
    "sqlite_db_folder": str(BASE_DIR / "hubdb"),
}


def _load_local_secret_settings():
    settings = {}
    secret_path = BASE_DIR / "secret_config.local.txt"
    if not secret_path.exists():
        return settings
    for line in secret_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        settings[key.strip()] = value.strip().strip("'").strip('"')
    return settings


DATA_HUB_DB_DATABASE = ".hubdb"
DATA_SRC_SERVER = "localhost"
DATA_SRC_DATABASE = "meastech_src"
DATA_TARGET_SERVER = "localhost"
DATA_TARGET_DATABASE = "meastech"

_LOCAL_SECRETS = _load_local_secret_settings()
if "HUB_GUEST_PASSWORD" in _LOCAL_SECRETS:
    import crypt

    guest_hash = crypt.crypt(_LOCAL_SECRETS["HUB_GUEST_PASSWORD"], crypt.mksalt(crypt.METHOD_SHA512))
    HUB_PASSWD = {"guest": guest_hash}
elif "HUB_GUEST_CRYPT" in _LOCAL_SECRETS:
    HUB_PASSWD = {"guest": _LOCAL_SECRETS["HUB_GUEST_CRYPT"]}

# biothings 0.12.3 expects hub DB client to expose an "address" attribute when
# creating uploaders. sqlite3 backend client doesn't implement it, so provide a
# local compatibility shim for no-Mongo setups.
import biothings.utils.sqlite3 as bt_sqlite3

if not hasattr(bt_sqlite3.DatabaseClient, "address"):
    bt_sqlite3.DatabaseClient.address = property(lambda self: self.sqlite_db_folder)

# Elasticsearch target (adjust for your environment).
ES_HOST = "http://localhost:9200"
ES_INDEX = "meastech_current"
ES_DOC_TYPE = "_doc"

ANNOTATION_DEFAULT_SCOPES = ["label", "synonyms", "curie"]
