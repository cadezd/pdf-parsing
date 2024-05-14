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


def get_x_column_border_coordinate(pdf_words: list[dict]) -> float:
    # get min x1 coordinate
    min_x0 = min([word['x0'] for word in pdf_words])
    # get max x1 coordinate
    max_x1 = max([word['x1'] for word in pdf_words])

    # get the middle between min x1 and max x1
    middle = (min_x0 + max_x1) / 2

    return middle


def sort_words(pdf_words: list[dict]) -> list[dict]:
    # get the last occurrence of the word "Seja" on the pdf
    last_seja_occurrence = None
    for word in pdf_words:
        if word['text'].lower() in {"konec", "javna", "seja", "konča"}:
            last_seja_occurrence = word

    bottom = last_seja_occurrence['top']
    last_page_no = last_seja_occurrence['page_no']

    # sort words on each page by column
    sorted_words = []
    page_numbers = sorted(list(set([word['page_no'] for word in pdf_words])))

    for page_no in page_numbers:
        words_on_same_page = [word for word in pdf_words if word['page_no'] == page_no]

        middle = get_x_column_border_coordinate(words_on_same_page)

        if page_no != last_page_no:
            left_column_words = [word for word in words_on_same_page if word['x1'] < middle]
            right_column_words = [word for word in words_on_same_page if word['x0'] >= middle]
            sorted_words.extend(left_column_words + right_column_words)
        else:
            left_column_words = [word for word in words_on_same_page if word['x1'] < middle and word['bottom'] < bottom]
            right_column_words = [word for word in words_on_same_page if
                                  word['x0'] >= middle and word['bottom'] < bottom]
            bottom_words = [word for word in words_on_same_page if word['bottom'] >= bottom]
            sorted_words.extend(left_column_words + right_column_words + bottom_words)

    return sorted_words


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


def get_len_of_n_next_words(query: str, idx: int, n: int) -> int:
    query_tmp = query[idx:]
    words = query_tmp.split()
    end_idx = min(n, len(words))
    return sum([len(word) for word in words[:end_idx]])


def get_len_of_n_previous_words(query: str, idx: int, n: int) -> int:
    query_tmp = query[:idx]
    words = query_tmp.split()
    start_idx = max(0, len(words) - n)
    return sum([len(word) for word in words[start_idx:]])


def main():
    script_reader: ScriptReader = ScriptReader(
        './testing_xml',
        './testing_pdf',
        _idx=6
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
            # get the last occurrence of the word "Seja" on the pdf
            for page_no, pdf_page in enumerate(pdf.pages[1:]):
                # get all words on the page and sort them by column
                page_words = pdf_page.extract_words()
                if page_words:
                    page_words: list[dict] = pdf_page.extract_words()
                    # add page number to each word
                    page_words = [{'page_no': page_no, **word} for word in page_words]
                    pdf_words.extend(page_words)
                else:
                    continue

        pdf_words = sort_words(pdf_words)

        bbxs: list[tuple[int, float, float, float, float]] = []

        # all words from pdf concatenated
        query: str = ' '.join([w['text'] for w in pdf_words])

        # indexes of the best match
        best_match_start: int = 0
        best_match_end: int = 0

        # indexes of the search area
        idx_search_start: int = 0
        idx_search_end: int = 0
        WORD_BUFFER_FORDWARDS: int = 20
        WORD_BUFFER_BACKWARDS: int = 0

        # similarity threshold
        THRESHOLD: float = 0.8

        try:
            while sentences_str:
                # miss counter
                MISS: int = 0

                # sentence from xml that we want to find in the pdf
                target: str = sentences_str.pop(0)

                # adjust searching area while searching for the target sentence
                while True:
                    # limiting the search of the target sentence to a certain area
                    idx_search_start = best_match_end
                    idx_search_end = (best_match_end +
                                      len(target) +
                                      get_len_of_n_next_words(query, best_match_end, WORD_BUFFER_FORDWARDS))
                    query_limited: str = query[idx_search_start:idx_search_end]

                    # print("QUERY LIMITED:", query_limited)

                    # getting best match indexes
                    # and adding idx_search_start to them, because we limited the search area
                    result = edlib.align(target, query_limited, task="path", mode="HW")

                    similarity = max(1 - result['editDistance'] / len(target), 0)

                    # when you get a good enough match
                    # break and reset the WORD_BUFFER_FORDWARDS, WORD_BUFFER_BACKWARDS and MISS counter
                    if similarity >= THRESHOLD:
                        best_match_start = idx_search_start + result['locations'][0][0]
                        best_match_end = idx_search_start + result['locations'][0][-1]
                        print(
                            f'{target} -> {best_match_start, best_match_end} -> {query[best_match_start:best_match_end]} -> {similarity}')
                        WORD_BUFFER_FORDWARDS = 10
                        WORD_BUFFER_BACKWARDS = 0
                        break
                    else:
                        if MISS > 15:
                            WORD_BUFFER_BACKWARDS += 5
                            print(f'{target} -> NOT FOUND')
                            break
                        else:
                            # increase the search area forwards
                            WORD_BUFFER_FORDWARDS += 5

                        MISS += 1

                # getting data for the bounding box for the target sentence
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
