"""BioThings uploader for BAO."""

from biothings.hub.dataload.uploader import BaseSourceUploader

from plugins._mapping import BASE_MAPPING


class BAOUploader(BaseSourceUploader):
    name = "bao"
    __metadata__ = {
        "src_name": "bao",
        "src_url": "https://www.bioassayontology.org/",
        "license_url": "https://www.bioassayontology.org/",
    }

    @classmethod
    def get_mapping(cls):
        return BASE_MAPPING
