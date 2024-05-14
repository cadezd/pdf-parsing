import traceback
import xml.etree.ElementTree as ET

import edlib
import pdfplumber

from ScriptReader import ScriptReader
from XMLEditor import XMLEditor

# tags of elements that contain text
TAGS: list[str] = ['s']
TAGS: list[str] = ['{http://www.tei-c.org/ns/1.0}' + tag for tag in TAGS]
# tags of elements that should be ignored (metadata)
IGNORE_TAGS: list[str] = ['note']
IGNORE_TAGS: list[str] = ['{http://www.tei-c.org/ns/1.0}' + tag for tag in IGNORE_TAGS]

CAHRS_THAT_INDICATE_NEW_LINE: set[str] = {'­', '-', '—', '*'}
CAHRS_THAT_INDICATE_END_OF_SENTENCE: set[str] = {'.', '?', '!'}

THRESHOLD: float = 0.75


def get_x_column_border_coordinate(pdf_words: list[dict]) -> float:
    # get min x1 coordinate
    min_x0 = min([word['x0'] for word in pdf_words])
    # get max x1 coordinate
    max_x1 = max([word['x1'] for word in pdf_words])

    # get the middle between min x1 and max x1
    middle = (min_x0 + max_x1) / 2

    return middle


def sort_words_by_column(pdf_words: list[dict]) -> list[dict]:
    middle = get_x_column_border_coordinate(pdf_words)
    left_column_word = [word for word in pdf_words if word['x1'] < middle]
    right_column_word = [word for word in pdf_words if word['x0'] >= middle]

    return left_column_word + right_column_word


def get_text_from_element(element: ET.Element) -> str:
    if element.tag == '{http://www.tei-c.org/ns/1.0}note':
        return element.text
    else:
        sentence = ''
        for child in element.iter():
            if child.tag == '{http://www.tei-c.org/ns/1.0}w':
                # words
                sentence += ' ' + child.text
            else:
                # punctuations
                sentence += child.text

        return sentence.strip()


def get_chars_that_indicate_end_of_sentence(sentences: list[str]) -> set[str]:
    chars_that_indicate_end_of_sentence = set()
    for sentence in sentences:
        last_char = sentence[-1]
        if not last_char.isalnum():
            chars_that_indicate_end_of_sentence.add(last_char)

    return chars_that_indicate_end_of_sentence


def calculate_similarity(query: str, target: str) -> float:
    result = edlib.align(target, query, task="path", mode="NW")
    return 1 - result['editDistance'] / len(target)


def get_index_of_the_most_similar_word(idx: int, words: list[dict], target: str, lookahead: int = 5) -> int:
    similarity = float('-inf')
    most_similar_word_idx = idx

    for i, word in enumerate(words[idx:idx + lookahead]):
        similarity_tmp = calculate_similarity(word['text'], target)
        if similarity_tmp > similarity:
            similarity = similarity_tmp
            most_similar_word_idx = idx + i

    return most_similar_word_idx


def show_result(pdf_path: str, bbxs: list[tuple[int, float, float, float, float]], _from: int = -1, _to: int = -1):
    images = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[1:]:
            images.append(page.to_image(resolution=150))

    for page_no, x1, y1, x2, y2 in bbxs:
        images[page_no].draw_rect((x1, y1, x2, y2), stroke_width=1)

    _from = 0 if _from == -1 else _from
    _to = len(images) if _to == -1 else _to
    for i, image in enumerate(images[_from:_to]):
        image.show()


def main():
    script_reader: ScriptReader = ScriptReader(
        './testing_xml',
        './testing_pdf',
        _idx=30
    )

    SUCCESSFUL: int = 0
    UNSUCCESSFUL: int = 0

    for idx, (xml_file_path, pdf_file_path) in enumerate(script_reader.group_xml_pdf()):
        # get a list of sentence elements from xml and convert them to list of strings
        xml_editor: XMLEditor = XMLEditor(xml_file_path)
        sentences_ET: list[ET.Element] = xml_editor.get_elements_by_tags(TAGS)
        sentences_str: list[str] = [get_text_from_element(sentence) for sentence in sentences_ET]

        # get a list of all words in the pdf
        pdf_words: list[dict] = []
        with pdfplumber.open(pdf_file_path) as pdf:
            for page_no, pdf_page in enumerate(pdf.pages[1:]):
                # get all words on the page and sort them by column
                page_words = pdf_page.extract_words()
                if page_words:
                    page_words: list[dict] = sort_words_by_column(pdf_page.extract_words())
                    # add page number to each word
                    page_words = [{'page_no': page_no, **word} for word in page_words]
                    pdf_words.extend(page_words)
                else:
                    break

        bbxs: list[tuple[int, float, float, float, float]] = []
        query: str = ' '.join([w['text'] for w in pdf_words])

        sentence_order_no: dict = {}
        best_match_start: int = 0
        best_match_end: int = 0

        # TODO: dodelaj da je iskanje omejeno na določeno področje

        try:
            while sentences_str:
                target: str = sentences_str.pop(0)

                # since some sentences are equal
                # we must get the start and end indexes of the correct sentence
                if target in sentence_order_no:
                    sentence_order_no[target] += 1
                else:
                    sentence_order_no[target] = 1

                result = edlib.align(target, query, task="path", mode="HW",
                                     additionalEqualities=[('­', '-'), ('-', '­')])

                # print(f'{target} |', end=' ')
                # get best match indexes
                # correct_sentence_order_no = sentence_order_no[target] if sentence_order_no[target] < len(
                #    result['locations']) else len(result['locations']) - 1

                correct_sentence_order_no = sentence_order_no[target] - 1

                # handling when the line is split into two lines, but there is the exact same line but not split
                if correct_sentence_order_no >= len(result['locations']):
                    best_match = ''

                    length = len(target) - 1

                    # while best match does not contain chars that indicate new line
                    while not any(char in best_match for char in CAHRS_THAT_INDICATE_NEW_LINE) and length > 0:
                        tmp_target = target[:length] + '-' + target[length:]

                        result = edlib.align(tmp_target, query, task="path", mode="HW",
                                             additionalEqualities=[('­', '-'), ('-', '­')])

                        best_match_start = result['locations'][0][0]
                        best_match_end = result['locations'][0][-1]
                        best_match = query[best_match_start:best_match_end]

                        print(
                            f'{tmp_target} | {best_match} | {best_match_start} | {best_match_end} | {any(char in best_match for char in CAHRS_THAT_INDICATE_NEW_LINE)}')

                        length -= 1

                else:
                    best_match_start = result['locations'][correct_sentence_order_no][0]
                    best_match_end = result['locations'][correct_sentence_order_no][-1]

                    # get best match string
                    best_match = query[best_match_start:best_match_end]

                    # print(f'{best_match_start} | {best_match_end} | {best_match} ')
                    # print()

                idx = 0
                for word in pdf_words:
                    if best_match_start <= idx <= best_match_end:
                        bbxs.append((word['page_no'], word['x0'], word['top'], word['x1'], word['bottom']))
                        # print(word['text'])

                    if idx >= best_match_end:
                        break

                    idx += len(word['text']) + 1

                # print()

            print(f'WORKS ON {pdf_file_path}')
            SUCCESSFUL += 1
        except Exception as e:
            print(f'ERROR ON {pdf_file_path}')
            print(traceback.format_exc())
            UNSUCCESSFUL += 1

        # display the result
        show_result(pdf_file_path, bbxs)

    print()
    print(f'TOTAL: {SUCCESSFUL + UNSUCCESSFUL}')
    print(f'SUCCESSFUL: {SUCCESSFUL}')
    print(f'UNSUCCESSFUL: {UNSUCCESSFUL}')
    print(f'SUCCESSFUL: {SUCCESSFUL / (SUCCESSFUL + UNSUCCESSFUL) * 100}%')

if __name__ == '__main__':
    main()
