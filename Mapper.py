import xml.etree.ElementTree as ET


class Mapper:
    def __init__(self,
                 elements: list[ET.Element],
                 chars: list[tuple[str, int, list[float]]],
                 TAGS: list[str],
                 IGNORE_TAGS: list[str],
                 DONT_PROCESS_TAGS: list[str]):
        self.elements: list[ET.Element] = elements
        self.chars: list[tuple[str, int, list[float]]] = chars
        self.TAGS: list[str] = TAGS
        self.IGNORE_TAGS: list[str] = IGNORE_TAGS
        self.DONT_PROCESS_TAGS: list[str] = DONT_PROCESS_TAGS

        self.OCR_MISTAKES = {
            'm': ['n'],
            'n': ['u'],
            'r': [],
            'S': [],
            '0': [],
            '1': [],
            '2': [],
            '3': [],
            '4': [],
            '5': [],
            '6': [],
            '7': [],
            '8': [],
            '9': [],
        }

        # staring indexes after skipping header elements
        self.start_pdf_char_idx, self.start_xml_element_idx = self._skip_header_elements()

    def _skip_header_elements(self) -> tuple[int, int]:
        """Returns index of the first element that needs to be processed and associated pdf char"""
        xml_element_idx: int = 0
        pdf_char_idx: int = 0

        while self.elements[xml_element_idx].tag in self.DONT_PROCESS_TAGS:
            if not self.elements[xml_element_idx].text:
                xml_element_idx += 1
                continue

            pdf_char_idx = self._skip_element(self.elements[xml_element_idx], pdf_char_idx)
            xml_element_idx += 1

        return pdf_char_idx, xml_element_idx

    def _skip_element(self, element: ET.Element, curr_pdf_char_idx: int, _print=False) -> int:
        """Returns index of the of pdf_char after skipping length(element.text) chars"""
        xml_char_idx: int = 0
        while xml_char_idx < len(element.text):
            xml_char = element.text[xml_char_idx]
            pdf_char, page_num, bbox = self.chars[curr_pdf_char_idx]

            try:
                # updating indexes
                curr_pdf_char_idx, xml_char_idx = self._move_indexes(
                    xml_char, pdf_char,
                    curr_pdf_char_idx,
                    xml_char_idx,
                    page_num,
                    _print=_print
                )
            except ValueError as e:
                raise ValueError(
                    f'Missmatch tag:{element.tag} xml: {xml_char}, pdf: {pdf_char}, page: {page_num}'
                )

        return curr_pdf_char_idx

    def _move_indexes(self, xml_char: str, pdf_char: str, curr_pdf_char_idx: int, xml_char_idx: int, page_no: int,
                      _print=False) -> tuple[int, int]:
        """"Returns updated indexes after comparing xml_char and pdf_char"""
        if xml_char == pdf_char:
            if _print:
                print(f'xml: {xml_char:<8} pdf: {pdf_char:<8} page_no:{page_no:<8} pdf_idx: {curr_pdf_char_idx:<12}')
            curr_pdf_char_idx += 1
            xml_char_idx += 1
        elif pdf_char in self.OCR_MISTAKES:
            # handling OCR mistakes (m -> n, etc.)
            if xml_char in self.OCR_MISTAKES[pdf_char]:
                if _print:
                    print(
                        f'xml: {xml_char:<8} pdf: {pdf_char:<8} page_no:{page_no:<8} pdf_idx: {curr_pdf_char_idx:<12}')
                curr_pdf_char_idx += 1
                xml_char_idx += 1
            else:
                # we assume that there is extra character in pdf
                curr_pdf_char_idx += 1
        else:
            # SPECIAL CASES
            # handling extra non-alphanumeric characters in pdf
            curr_pdf_char_idx += 1
            """
            if not pdf_char.isalnum():
                curr_pdf_char_idx += 1
            else:
                raise ValueError(f'Missmatch xml: {xml_char}, pdf: {pdf_char}')
            """

        return curr_pdf_char_idx, xml_char_idx

    def add_data_to_elements(self, _print=False) -> None:
        """Adds data to elements from pdf_chars and prints elements with their attributes"""
        pdf_char_idx = self.start_pdf_char_idx
        for xml_element_idx, element in enumerate(self.elements[self.start_xml_element_idx:]):

            # skipping elements without text
            if not element.text:
                continue

            # skipping elements that shouldn't be processed
            if element.tag in self.DONT_PROCESS_TAGS:
                if _print:
                    print(f'Skipping element: {element.text}')
                pdf_char_idx = self._skip_element(element, pdf_char_idx, _print=_print)
                continue

            # getting data for each element (fromPage, toPage, x1, y1)
            if _print:
                print(element.text)
            xml_char_idx = 0
            while xml_char_idx < len(element.text) and pdf_char_idx < len(self.chars):
                xml_char = element.text[xml_char_idx]
                pdf_char, page_num, bbox = self.chars[pdf_char_idx]

                if  pdf_char == xml_char:
                    element.set('fromPage', int(page_num))
                    element.set('x1', int(bbox[0]))
                    element.set('y1', int(bbox[1]))

                try:
                    # updating indexes
                    pdf_char_idx, xml_char_idx = self._move_indexes(
                        xml_char, pdf_char,
                        pdf_char_idx,
                        xml_char_idx,
                        page_num,
                        _print=_print
                    )

                except ValueError as e:
                    print(self.chars[pdf_char_idx:pdf_char_idx + 10])
                    raise ValueError(
                        str(e) + f' page: {page_num}'
                    )

            element.set('toPage', str(page_num))

            print()


        # printing elements
        attributes = ['fromPage', 'toPage', 'x1', 'y1']
        for item in self.elements[self.start_xml_element_idx:]:
            # priting elements text and attributes fromPage, toPage, x1, y1
            print(item.text, [(k, v) for k, v in item.items() if k in attributes])

