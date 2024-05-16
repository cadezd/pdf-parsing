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

SESSION_START_GER: set = {"Beginn", "Deginn", "Keginn", "Jeginn", "Heginn", "Begimi",
                          "eginn der Sitzung", "eginn der Zitzung", "Login» der Sitzung", "Britinn brv Sitzung",
                          "Dezinn litt fiUmtg", "Beginn -er Sitzung", "Deginu der Sitzung", "Leginn brv Sitzung",
                          "fSegtun der Sitzung um", "beginn Mr Sitzung um", "ßcijiim der Ätzung",
                          "fPiginu ber ^it)ung um", "glegtnn Per ¿Styling um", "Srginn der Sitzung",
                          "Region der Sitzung", "Leginn der Ätzung", "§ e p i i bet Sitzung", "Drginn der Sitzung",
                          "Hechln der Sitzung", "Srgtmt der Zitznng", "Hrginil d«tt Iibmig mit",
                          "Seginil der Sitzung", "Drginn dctt Aitrung", "örginn der Sitzung", "fkflinn her SKfeung",
                          "jßrgiim der Sitzung", "fUeflinn ber", "gigttttt bet §t|u«3", "Seginn bet Sitzung",
                          "Segiuu der Sitzung", "ßrgiim k r Sitzung", "§ r p it bor Sitzung", "beginn jSi^ung um",
                          "peginn her &itung", "ßrgiim kr Sitzung", "Beginn brr Zitznng", "Beginn brr Sitzung",
                          "Beginn der Ätzung", "ßegimt der Sitzung", "Dcginn der Sitzung", "Scgiitii brr Sitzung",
                          "Beginn der Kitznng", "Leginn drr Sitzung", "§epii bet Sitzung", "§rpit bor Sitzung",
                          "Äegiun -er Sitzung", "Mglmi der Sitzung mit", "Hegiml llq Kilrnng m\ 10",
                          "Hrgimi iln* Piirmig itiij 9", "Zcginn der Sitzung um 10", "§tgmit der Sitzung mit 10",
                          "Hcgiim litt! sibling MI, 11 Ht", "fegtmt ber §tipng 10 Uftjr",
                          "beginn lles sibling mg 9 Rhr", "Legi«« der Zitznng", "Scflinn der Ätzung",
                          "Stgintt der Ätzung um", "Ärginn der Sitzung", "Beginn !>er Sitzung", "Beginn der Zitznng",
                          "Beginn der öffentlichcii Sitzung", "Legiiin Der Sitzung", "Hrgmii der Sitzung um",
                          "beginn dttt Aiirung mit", "Scgtiiu der Sitzung", "Scgittn ber Strung",
                          "jBrginn der Sitzung um", "ßrßtntt der Zitziing", "Legi mi der Sitzung",
                          "Segiim der Sitzung", "Legiim ber Zitzimg", "I beginn tier Sitzung um",
                          "Dkginn brr Zihung um", "ßegiiin tier Sitzung", "§epm bet Sitzung um",
                          "Leginn der Litzung", "tu'if in n der Sitzung mn", "$t9inn btt giijuttg", "Mgiim",
                          "Helsinn der Sitzung", "Skginn brr Sitzung", "feptn der Sitzung um",
                          "beginn litt Illenng Nil,", "Zrginn der Sitzung", "Čcgimt der Sitzung",
                          "Scgtttn der Sitzung", "Krginn der Sitzung um", "Demi) der Sitzung um",
                          "Htginn litt: Stirling tut]", "Hechln ßer Sitzung um", "Hessinn riet sibling NN,",
                          "§tgimt der Sitzung, um", "ßrgtmi der Zitzmig", "Beginn der Litznng", "Srgiim der Sitzung",
                          "lepit der Sitzung um", "gegttm ber Snijuttg urn", "ßrgtnit der Sitzung",
                          "$eginn ber §üsuttg", "Uegiim 6cv Sitzung um", "Beginn 6er Sitzung",
                          "§fgmn bet Sitzung um", "(beginn der Litznng", "ßnjimi der Sitzung",
                          "Scginn der Sitzung um", "Legiim der Sitzung", "Mginn der Sitzung",
                          "Ürginn örv Sitzung mit", "Kegin» der Sitzung", "ißegitm in* Sitzung mit",
                          "Beginn bet Sitzung um", "Legiiin bcr Ätzung", "Lrginn der Zitzuiig",
                          "Beginn !>er Sitjumi", "Äeginu der Sitzung", "§egimt der Sitzung", "Leginn kr Sitzung NM",
                          "§tpm der Siting um", "Segiiin kr Zitznng", "Irginn der Sitzung m", "Seginn brr Sitzung",
                          "Iegimr der Sitzung um", "Srgtnti der Sitzung", "ßrgtttn der Sitzung",
                          "iltt fdbnittj} itttj 11 Ijljr", "Üegiun der Siijimg", "Beginn-erSitznng um",
                          "ßfßtntt der Sitzung", "gegttm ber giijimg", "Drginn dcr Sitzung", "legtntt in §tijung",
                          "Beginn der Sihung", "Üeginn t>cr Sitzung mu", "Lrginn der Sitzung",
                          "Zegiuu der Sitzung um", "Degiiiii der Sitzmß um", "Lrginn der Ätzung",
                          "jßrgtnn der Zitznng um", "gegiitn ber Biljung", "Scgiim der Ätzung", "Begin» der Sitzung",
                          "Äegiim der Kitzung", "Lcginn der Sitzung", "Beginn tier Kihnlig"}
SESSION_START_GER = {words.split(' ')[0] for words in SESSION_START_GER}

SESSION_START_SLO: set = {"Začetek seje", "Seja se začne", "Seja sa začne", "Začetek ob ", "Seja se-začne",
                          "Soja se začne", "Seja se prične", "Seja še začne", "8eja se začne", "Seja 8p začne",
                          "Seja se začue", "Javna seja se začne", "Seja 86 začne o", "Seja se začnč o",
                          "®eJa se začne ob", "Seja se začnd o", "Seja sc začne o"}
SESSION_START_SLO = {words.split(' ')[0] for words in SESSION_START_SLO}


def get_x_column_border_coordinate(pdf_words: list[dict]) -> float:
    # get min x1 coordinate
    min_x0 = min([word['x0'] for word in pdf_words])
    # get max x1 coordinate
    max_x1 = max([word['x1'] for word in pdf_words])

    # get the middle between min x1 and max x1
    middle = (min_x0 + max_x1) / 2

    return middle


def remove_header(pdf_words: list[dict]) -> list[dict]:
    # get the first occurrence of the word that indicates the beginning of the session
    session_begin_word = None
    for word in pdf_words:
        if word['text'].strip() in SESSION_START_GER.union(SESSION_START_SLO):
            session_begin_word = word
            break

    # get bottom coordinate of the session begin word
    BOTTOM = session_begin_word['bottom']
    # get the middle of the page
    MIDDLE = get_x_column_border_coordinate(pdf_words)

    # sort words that are below the header in two columns
    left_column_words = [word for word in pdf_words if word['x1'] < MIDDLE and word['bottom'] < BOTTOM]
    right_column_words = [word for word in pdf_words if word['x0'] >= MIDDLE and word['bottom'] < BOTTOM]

    return left_column_words + right_column_words


def get_text_from_element(element: ET.Element) -> str:
    if element.tag == '{http://www.tei-c.org/ns/1.0}note':
        return ''
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


def get_words_from_pdf(pdf_path: str) -> list[dict]:
    # get a list of all words in the pdf
    pdf_words: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:

        # remove header from the first page
        first_page: pdfplumber.page.Page = pdf.pages[0]
        first_page_words: list[dict] = first_page.extract_words(use_text_flow=True)
        first_page_words = remove_header(first_page_words)
        first_page_words = [{'page_no': 0, **word} for word in first_page_words]
        pdf_words.extend(first_page_words)

        # get all words from the rest of the pages
        for page_no, pdf_page in enumerate(pdf.pages[1:]):
            # get all words based on PDF's underlying flow of characters
            page_words: list[dict] = pdf_page.extract_words(use_text_flow=True)

            # add page number to each word it has text
            if page_words:
                page_words = [{'page_no': page_no, **word} for word in page_words]
                pdf_words.extend(page_words)
            else:
                continue

    return pdf_words


def main():
    script_reader: ScriptReader = ScriptReader(
        './testing_xml',
        './testing_pdf',
        _idx=1
    )

    SUCCESSFUL: int = 0
    UNSUCCESSFUL: int = 0

    for idx, (xml_file_path, pdf_file_path) in enumerate(script_reader.group_xml_pdf()):
        # get a list of sentence elements from xml and convert them to list of strings
        xml_editor: XMLEditor = XMLEditor(xml_file_path)
        sentences_ET: list[ET.Element] = xml_editor.get_elements_by_tags(TAGS)
        sentences_str: list[str] = [get_text_from_element(sentence) for sentence in sentences_ET]

        # get a list of all words in the pdf
        pdf_words: list[dict] = get_words_from_pdf(pdf_file_path)

        bbxs: list[tuple[int, float, float, float, float]] = []

        # all words from pdf concatenated
        query: str = ' '.join([w['text'] for w in pdf_words])

        word_occurrences: dict = dict()

        try:
            while sentences_str:

                # sentence from xml that we want to find in the pdf
                target: str = sentences_str.pop(0)

                # if the target contains any new line character, append the next sentence to it
                if any([char in CAHRS_THAT_INDICATE_NEW_LINE for char in target]):
                    if sentences_str:
                        target += ' ' + sentences_str.pop(0)

                if target in word_occurrences:
                    word_occurrences[target] += 1
                else:
                    word_occurrences[target] = 0

                # adjust searching area while searching for the target sentence

                # getting best match indexes
                # and adding idx_search_start to them, because we limited the search area
                result = edlib.align(target, query, task="path", mode="HW")

                similarity = max(1 - result['editDistance'] / len(target), 0)

                i = word_occurrences.get(target, 0)
                print(i)
                best_match_start = result['locations'][i][0]
                best_match_end = result['locations'][i][-1]
                print(
                    f'{target} -> {best_match_start, best_match_end} -> {query[best_match_start:best_match_end]} -> {similarity}')

                # getting data for the bounding box for the target sentence
                idx = 0
                for word in pdf_words:
                    if best_match_start <= idx <= best_match_end:
                        bbxs.append((word['page_no'], word['x0'], word['top'], word['x1'], word['bottom']))
                    if idx >= best_match_end:
                        break
                    idx += len(word['text']) + 1

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
