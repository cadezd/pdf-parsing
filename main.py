import xml.etree.ElementTree as ET

import pdfplumber

from ScriptReader import ScriptReader
from XMLEditor import XMLEditor


def show_result(pdf_file_path: str, bbx: list[tuple[int, int, float, float, float, float]], resolution: int = 150,
                offset: int = 0, stroke: str = 'red'):
    images = []
    with pdfplumber.open(pdf_file_path) as pdf:
        for page in pdf.pages[offset:]:
            images.append(page.to_image(resolution=resolution))

    for fromPage, toPage, isWordOnMultipleLines, x1, y1, x2, y2, x3, y3, x4, y4 in bbx:

        # skipping elements that were not found in the pdf
        if fromPage == 99999 or toPage == -99999 or (x1 == float('inf') and x3 == float('inf')):
            continue

        # drawing bounding boxes
        if not x1 == float('inf'):
            images[fromPage - (1 + offset)].draw_rect(
                (x1, y1, x2, y2),
                stroke_width=1,
                stroke=stroke
            )

        # drawing extra bounding box for words that are on multiple lines
        if not x3 == float('inf'):
            images[fromPage - (1 + offset)].draw_rect(
                (x3, y3, x4, y4),
                stroke_width=1,
                stroke=stroke
            )

    for image in images:
        image.show()


def main():
    # tags of elements that contain text
    TAGS: list[str] = ['w', 'pc', 'title', 'head', 'label', 'item', 'note', 'meeting']
    TAGS: list[str] = ['{http://www.tei-c.org/ns/1.0}' + tag for tag in TAGS]
    # tags of elements that should be ignored (metadata)
    IGNORE_TAGS: list[str] = ['teiHeader']
    IGNORE_TAGS: list[str] = ['{http://www.tei-c.org/ns/1.0}' + tag for tag in IGNORE_TAGS]
    # tags that contain text but shouldn't be processed
    DONT_PROCESS_TAGS: list[str] = ['title', 'head', 'label', 'item', 'note', 'meeting', 'pc']
    DONT_PROCESS_TAGS: list[str] = ['{http://www.tei-c.org/ns/1.0}' + tag for tag in DONT_PROCESS_TAGS]

    CAHRS_THAT_INDICATE_NEW_LINE: list[str] = ['­', '-', '—', '*']
    CHARS_TO_SKIP: list[str] = ['<', '>', '^', '(', ')', '&', '-', '»', '\'', '.', '|', ',', '$', '#', '/', '%', ':',
                                '!', ';', '\\', '\"', '=', '+', '?', ']', '[', '{', '}', '@', '§', '°', '€', '£', '¥',
                                '■', '•', '~', '´', '`', '¨', '¬', '¦', '©', '®', '™', '±', '×', '÷', 'µ', '¶', '§',
                                '†', '‡', '°', '¢', '¤', '«', '»', '‹', '›', '„', '“', '”', '‘', '’', '‚', '…', '–',
                                '¿', '_', '♦']

    # words that were messed up in the xml during sentence analysis (xml word, pdf word)
    WRONG_WORDS_IN_XML: dict[str, str] = {
        'üea': 'unterm',
        'üuf': 'fürs',
    }

    # words that are different in the pdf because of the sentence analysis (xml word, possible pdf words)
    POSSIBLE_ENDINGS: dict[str, set[str]] = {
        'zu': {'r', 'm'},
        'an': {'u', 's'},
        'bei': {'m', },
        'in': {'s'},
    }

    WRONG_WORD_ENDINGS: dict[str, set[str | int]] = {
        'von': {'m', 'n'},
        'un': {'m', 'n'},
        'an': {'m', 'n'},
        'in': {'m', 'n'},
        'vn': {-1},
        'bei': {'d', 'e', 'm'},
        'voei': {'v', 'o', 'l', 'e', 'm'}
    }

    script_reader: ScriptReader = ScriptReader(
        './testing_xml',
        './testing_pdf',
        _idx=3
    )

    for idx, (xml_file_path, pdf_file_path) in enumerate(script_reader.group_xml_pdf()):

        try:
            # DIFFERENT TRIES
            xml_editor: XMLEditor = XMLEditor(xml_file_path)
            # gets elements that contain text specified by TAGS
            # ignores elements specified by IGNORE_TAGS (metadata)
            elements: list[ET.Element] = xml_editor.get_elements_by_tags(TAGS, ignore_tags=IGNORE_TAGS)

            # filter header elements (firs n element in the DONT_PROCESS_TAGS)
            while elements[0].tag in DONT_PROCESS_TAGS:
                # if element has attribute 'type' of 'speaker' it not a header element so break
                if elements[0].get('type', '') == 'speaker':
                    break
                elements.pop(0)

            with (pdfplumber.open(pdf_file_path) as pdf):
                # check last page if there is more than one 70% of characters that are not alphanumeric remove it
                # if len([char for char in pdf.pages[-1].chars if not char['text'].isalnum()]) > 0.7 * len(pdf.pages[-1].chars):
                #    pdf.pages.pop(-1)

                # one list of all pdf characters
                pdf_chars: list[list[dict]] = [pdf.chars for pdf in pdf.pages[1:]]
                pdf_chars: list[dict] = [char for page in pdf_chars for char in page]

                # list of bounding boxes of words
                bbx: list[tuple[
                    int, int, bool, float, float, float, float, float, float, float, float]
                ] = []

                i = 0  # index for elements
                j = 0  # index for pdf_chars
                while i < len(elements) and j < len(pdf_chars):

                    # ignore header element
                    if elements[i].tag == '{http://www.tei-c.org/ns/1.0}head':
                        i += 1
                        continue

                    # correction element text if it is in DIFERENT_WORDS_IN_XML
                    element: ET.Element = elements[i]
                    element.text = WRONG_WORDS_IN_XML.get(element.text.lower(), element.text)

                    xml_chars: list[str] = list(element.text)

                    k = 0  # index for xml_chars
                    # data to add to the element
                    isWordOnMultipleLines: bool = False
                    fromPage: int = 99999
                    toPage: int = -99999
                    x1: float = float('inf')
                    y1: float = float('inf')
                    x2: float = float('-inf')
                    y2: float = float('-inf')
                    x3: float = float('inf')
                    y3: float = float('inf')
                    x4: float = float('-inf')
                    y4: float = float('-inf')

                    print(element.text)

                    while j < len(pdf_chars) and k < len(xml_chars):
                        pdf_char: str = pdf_chars[j]['text']
                        xml_char: str = xml_chars[k]
                        page_number: int = pdf_chars[j]['page_number']

                        print(f'{xml_char:<3} {pdf_char:<3} {page_number:<3}')

                        if pdf_char == xml_char or pdf_char in WRONG_WORD_ENDINGS.get(
                                element.text.lower(), set()):

                            fromPage = min(fromPage, page_number)
                            toPage = max(toPage, page_number)

                            # checking if one word has space that is braking it in two lines
                            if i - 1 > 0 and \
                                    elements[i - 1].tag == '{http://www.tei-c.org/ns/1.0}w' and \
                                    ' ' in element.text and \
                                    round(pdf_chars[j - 1]['top'], 2) != round(pdf_chars[j]['top'], 2):
                                isWordOnMultipleLines = True

                            # handling words that are on the same line
                            if not isWordOnMultipleLines:
                                x1 = round(min(x1, pdf_chars[j]['x0']), 2)
                                y1 = round(min(y1, pdf_chars[j]['top']), 2)
                                x2 = round(max(x2, pdf_chars[j]['x1']), 2)
                                y2 = round(max(y2, pdf_chars[j]['bottom']), 2)

                            # handling words that are on multiple lines
                            else:
                                x3 = round(min(x3, pdf_chars[j]['x0']), 2)
                                y3 = round(min(y3, pdf_chars[j]['top']), 2)
                                x4 = round(max(x4, pdf_chars[j]['x1']), 2)
                                y4 = round(max(y4, pdf_chars[j]['bottom']), 2)

                            # print(f'{xml_char:<3} {pdf_char:<3} {page_number:<3}')

                            k += 1
                            j += 1

                        else:
                            # HANDLING SPECIAL CASES
                            # same word can have different endings in pdf (von in xml can be von or vom in pdf)
                            if elements[
                                i].text.lower() in WRONG_WORD_ENDINGS.keys() and pdf_char in WRONG_WORD_ENDINGS.get(
                                elements[i].text.lower(), set()):
                                k += 1
                                j += 1
                                continue

                            # extra character in xml because of sentence analysis (e.g. 'vn' in xml is 'v' in pdf)
                            if elements[i].text.lower() in WRONG_WORD_ENDINGS.keys() and -1 in WRONG_WORD_ENDINGS.get(
                                    elements[i].text.lower(), set()):
                                k += len(elements[i].text)
                                continue

                            # extra character in pdf because of sentence analysis
                            if i - 1 >= 0 and elements[i - 1].text.lower() in POSSIBLE_ENDINGS.keys() and pdf_char in \
                                    POSSIBLE_ENDINGS[elements[i - 1].text.lower()]:
                                j += 1
                                continue

                            # extra space in xml
                            if xml_char.isspace():
                                k += 1
                                continue

                            # extra space in pdf
                            if pdf_char.isspace():
                                j += 1
                                continue

                            # word is split in two lines
                            if pdf_char in CAHRS_THAT_INDICATE_NEW_LINE \
                                    and j + 1 < len(pdf_chars) \
                                    and pdf_chars[j + 1]['top'] > pdf_chars[j]['top']:
                                isWordOnMultipleLines = True
                                j += 1
                                continue

                            # extra character in pdf
                            if pdf_char.isalnum() and xml_char.isalnum() and pdf_char.lower() != xml_char.lower():
                                j += 1
                                continue

                            # special characters in pdf that should be skipped
                            if pdf_char in CHARS_TO_SKIP:
                                j += 1
                                continue

                            # special characters in xml that should be skipped
                            if xml_char in CHARS_TO_SKIP:
                                k += 1
                                continue

                            # extra numeric character in pdf
                            if pdf_char.isnumeric() and not xml_char.isnumeric():
                                j += 1
                                continue

                            # extra numeric character in xml
                            if xml_char.isnumeric() and not pdf_char.isnumeric():
                                k += 1
                                continue

                            raise Exception(f'{xml_char:<3} {pdf_char:<3} {page_number:<3} MISTAKE')

                    # adding bounding box to the element as attributes
                    # adding bounding box to the list
                    if element.tag not in DONT_PROCESS_TAGS:
                        element.set('fromPage', str(fromPage))
                        element.set('toPage', str(toPage))
                        element.set('isBroken', str(isWordOnMultipleLines))
                        element.set('x1', str(x1))
                        element.set('y1', str(y1))
                        element.set('x2', str(x2))
                        element.set('y2', str(y2))

                        # adding extra bounding box for words that are on multiple lines
                        if isWordOnMultipleLines:
                            element.set('x3', str(x3))
                            element.set('y3', str(y3))
                            element.set('x4', str(x4))
                            element.set('y4', str(y4))

                        bbx.append(
                            (fromPage, toPage, isWordOnMultipleLines, x1, y1, x2, y2, x3, y3, x4, y4)
                        )

                    print()
                    i += 1

            # shows the mapping of the elements to the pdf
            show_result(pdf_file_path, bbx, offset=1)

            # adding coordinates to the sentences (based on words attributes)
            xml_editor.add_coordinates_to_sentences()

            # adding coordinates to the segments (based on sentences attributes)
            xml_editor.add_coordinates_to_segments()

            # saving the xml file
            xml_editor.save('./output')

        except Exception as e:
            print(e)
            print(idx, "Mistake in file: ", xml_file_path, pdf_file_path)
            continue


if __name__ == '__main__':
    main()
