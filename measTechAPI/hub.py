"""Run a local BioThings Hub for measTech plugins."""

import plugins
from biothings.hub import HubServer


class MeasTechHubServer(HubServer):
    # Avoid autohub command wiring, which is buggy in biothings 0.12.3 minimal setups.
    DEFAULT_FEATURES = [
        "config",
        "job",
        "dump",
        "upload",
        "dataplugin",
        "source",
        "build",
        "diff",
        "index",
        "snapshot",
        "release",
        "inspect",
        "sync",
        "api",
        "terminal",
        "reloader",
        "dataupload",
        "ws",
        "readonly",
        "upgrade",
        "hooks",
    ]


FEATURES = [
    "job",
    "dump",
    "upload",
    "source",
    "build",
    "terminal",
    "ws",
]


def main():
    hub = MeasTechHubServer(
        source_list=[plugins],
        features=FEATURES,
        name="measTech BioThings Hub",
    )
    hub.configure()
    hub.start()


if __name__ == "__main__":
    main()
