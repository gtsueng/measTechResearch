"""BioThings uploader for EDAMT."""

from biothings.hub.dataload.uploader import BaseSourceUploader

from plugins._mapping import BASE_MAPPING


class EDAMTUploader(BaseSourceUploader):
    name = "edamt"
    __metadata__ = {
        "src_name": "edamt",
        "src_url": "https://edamontology.org/",
        "license_url": "https://edamontology.org/",
    }

    @classmethod
    def get_mapping(cls):
        return BASE_MAPPING
