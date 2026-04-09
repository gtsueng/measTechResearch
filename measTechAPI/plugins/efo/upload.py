"""BioThings uploader for EFO."""

from biothings.hub.dataload.uploader import BaseSourceUploader

from plugins._mapping import BASE_MAPPING


class EFOUploader(BaseSourceUploader):
    name = "efo"
    __metadata__ = {
        "src_name": "efo",
        "src_url": "https://www.ebi.ac.uk/efo/",
        "license_url": "https://www.ebi.ac.uk/efo/",
    }

    @classmethod
    def get_mapping(cls):
        return BASE_MAPPING
