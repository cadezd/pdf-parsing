import re
from pathlib import Path


class ScriptReader:
    def __init__(self, xml_folder: str, pdfs_folder: str, _idx: int = -1, _from: int = -1, _to: int = -1):
        self.xml_folder: str = xml_folder
        self.pdfs_folder: str = pdfs_folder
        self._idx: int = _idx
        self._from: int = _from
        self._to: int = _to

        if self._from > self._to:
            raise ValueError('From must be less than to')

        self.XML_FILTER = re.compile('DezelniZborKranjski-[0-9]{8}-[0-9]{2}-[0-9]{2}\\.tei\\.xml')
        self.PDF_FILTER = re.compile('DezelniZborKranjski-[0-9]{8}-[0-9]{2}-[0-9]{2}\\.pdf')

    def group_xml_pdf(self) -> list[tuple[str, str]]:
        """
        Returns path to xml and associated pdf file
        :return: list[tuple[str, str]]
        """

        xml_files = sorted(Path(self.xml_folder).rglob('*.xml'))
        pdf_files = sorted(Path(self.pdfs_folder).rglob('*.pdf'))

        xml_files = [str(f) for f in xml_files if self.XML_FILTER.match(f.name)]
        pdf_files = [str(f) for f in pdf_files if self.PDF_FILTER.match(f.name)]

        if self._idx != -1:
            xml_files = [xml_files[self._idx]]
            pdf_files = [pdf_files[self._idx]]

        elif self._from != -1 and self._to != -1:
            xml_files = xml_files[self._from:self._to]
            pdf_files = pdf_files[self._from:self._to]


        return list(zip(xml_files, pdf_files))
