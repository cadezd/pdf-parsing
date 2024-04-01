import xml.etree.ElementTree as ET

import pdfplumber

from ScriptReader import ScriptReader
from XMLEditor import XMLEditor


def show_result(pdf_file_path: str, bbx: list[tuple[int, int, float, float, float, float]], resolution: int = 150,
                offset: int = 0):
    images = []
    with pdfplumber.open(pdf_file_path) as pdf:
        for page in pdf.pages[offset:]:
            images.append(page.to_image(resolution=resolution))

    for fromPage, toPage, x1, y1, x2, y2 in bbx:
        # if element wasn't something went wrong so break
        if x1 == float('inf') or y1 == float('inf') or x2 == float('-inf') or y2 == float('-inf'):
            break

        images[fromPage - (1 + offset)].draw_rect((x1, y1, x2, y2), fill=None, stroke_width=1)

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

    OCR_MISTAKES: dict[str, list[str]] = {
        'm': ['n']
    }

    script_reader: ScriptReader = ScriptReader('./testing_xml', './testing_pdf', _idx=2)

    for xml_file_path, pdf_file_path in script_reader.group_xml_pdf():

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

        with pdfplumber.open(pdf_file_path) as pdf:
            # one list of all pdf characters
            pdf_chars: list[list[dict]] = [pdf.chars for pdf in pdf.pages[1:]]
            pdf_chars: list[dict] = [char for page_chars in pdf_chars for char in page_chars]

            bbx = []

            i = 0  # index for elements
            j = 0  # index for pdf_chars
            while i < len(elements):
                element: ET.Element = elements[i]
                xml_chars: list[str] = list(element.text)

                k = 0  # index for xml_chars
                # data to add to the element
                fromPage, toPage = float('inf'), float('-inf')
                x1, y1, x2, y2 = float('inf'), float('inf'), float('-inf'), float('-inf')

                print(element.text)

                while j < len(pdf_chars) and k < len(xml_chars):
                    pdf_char: str = pdf_chars[j]['text']
                    xml_char: str = xml_chars[k]
                    page_number: int = pdf_chars[j]['page_number']

                    fromPage = min(fromPage, page_number)
                    toPage = max(toPage, page_number)
                    x1 = round(min(x1, pdf_chars[j]['x0']), 2)
                    y1 = round(min(y1, pdf_chars[j]['top']), 2)
                    x2 = round(max(x2, pdf_chars[j]['x1']), 2)
                    y2 = round(max(y2, pdf_chars[j]['bottom']), 2)

                    if pdf_char == xml_char or pdf_char in OCR_MISTAKES.keys():
                        print(f'{xml_char:<3} {pdf_char:<3} {page_number:<3}')
                        k += 1
                        j += 1

                    else:
                        # print(f'{xml_char:<3} {pdf_char:<3} {page_number:<3} MISTAKE')
                        j += 1

                # adding bounding box to the element as attributes
                # adding bounding box to the list
                if element.tag not in DONT_PROCESS_TAGS:
                    element.set('fromPage', str(fromPage))
                    element.set('toPage', str(toPage))
                    element.set('x1', str(x1))
                    element.set('y1', str(y1))
                    element.set('x2', str(x2))
                    element.set('y2', str(y2))
                    bbx.append((fromPage, toPage, x1, y1, x2, y2))

                print()
                i += 1

        # shows the mapping of the elements to the pdf
        show_result(pdf_file_path, bbx, offset=1)

        # saving the xml file
        #xml_editor.save('./output')


if __name__ == '__main__':
    main()
