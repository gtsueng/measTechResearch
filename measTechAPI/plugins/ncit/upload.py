"""BioThings uploader for NCIT."""

from biothings.hub.dataload.uploader import BaseSourceUploader

from plugins._mapping import BASE_MAPPING


class NCITUploader(BaseSourceUploader):
    name = "ncit"
    __metadata__ = {
        "src_name": "ncit",
        "src_url": "https://ncit.nci.nih.gov/",
        "license_url": "https://evs.nci.nih.gov/ftp1/NCI_Thesaurus/",
    }

    @classmethod
    def get_mapping(cls):
        return BASE_MAPPING
