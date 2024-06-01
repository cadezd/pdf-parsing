import os.path
import shutil
import traceback
import xml.etree.ElementTree as ET

import edlib
import pdfplumber

from ScriptReader import ScriptReader
from XMLEditor import XMLEditor

# tags of elements that contain text
SENTENCE_TAG: list[str] = ['s']
SENTENCE_TAG: list[str] = ['{http://www.tei-c.org/ns/1.0}' + tag for tag in SENTENCE_TAG]
# tags of elements that should be ignored (metadata)
NOTE_TAG: list[str] = ['note']
NOTE_TAG: list[str] = ['{http://www.tei-c.org/ns/1.0}' + tag for tag in NOTE_TAG]

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

BUFFER_LIMIT: int = 200


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


def prepare_result(xml_path: str, pdf_path: str, bbxs: list[tuple[int, float, float, float, float]], _from: int = -1,
                   _to: int = -1):
    # create folder from the xml file name in the results folder
    file_name = os.path.basename(xml_path).split('.')[0]
    folder = os.path.join('./results', file_name)
    os.makedirs(folder, exist_ok=True)

    images = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[1:]:
            images.append(page.to_image(resolution=150))

    for page_no, x1, y1, x2, y2 in bbxs:
        images[page_no].draw_rect((x1, y1, x2, y2), stroke_width=1)

    # save the images with the bounding boxes in the folder
    for idx, image in enumerate(images):
        image.save(os.path.join(folder, f'{file_name}_{idx}.png'))


def get_words_from_pdf(pdf_path: str) -> list[dict]:
    # get a list of all words in the pdf
    pdf_words: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
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

    # TODO: dodelaj da odstrani vse besede pred prvo pojavitvijo besede seja in po zadnji besedi seja

    return pdf_words


def get_len_of_next_n_words(query: str, idx: int, n: int) -> int:
    words = query[idx:].split(' ')
    return sum([len(word) + 1 for word in words[:n]])


def get_len_of_next_sentence(query: str, idx: int) -> int:
    words = query[idx:].split(' ')
    s = 0
    for word in words:
        # check if the word contains a character that indicates the end of the sentence
        if any(char in word for char in CAHRS_THAT_INDICATE_END_OF_SENTENCE):
            s += len(word) + 1
            break

        s += len(word) + 1

    return s


def handle_exception(pdf_words: list[dict], sentences_str: list[str]) -> list[
    tuple[int, float, float, float, float]]:
    bbxs: list[tuple[int, float, float, float, float]] = []

    # all words from pdf concatenated
    query: str = ' '.join([w['text'] for w in pdf_words])

    best_match_start: int = 0
    best_match_end: int = 0

    result = {'locations': []}
    search_area_start: int = 0

    while sentences_str:
        # sentence from xml that we want to find in the pdf
        target: str = sentences_str.pop(0)
        similarity: float = 0
        BUFFER: int = 10

        no_of_words = len(target.split(' '))
        if no_of_words == 1:
            SIMILARITY_THRESHOLD = 0.25
        elif 1 < no_of_words < 5:
            SIMILARITY_THRESHOLD = 0.6
        elif 5 <= no_of_words < 10:
            SIMILARITY_THRESHOLD = 0.7
        elif 10 <= no_of_words < 20:
            SIMILARITY_THRESHOLD = 0.75
        else:
            SIMILARITY_THRESHOLD = 0.8

        while similarity < SIMILARITY_THRESHOLD:
            # adjust searching area while searching for the target sentence
            search_area_start = best_match_end
            search_area_end = search_area_start + len(target) + get_len_of_next_n_words(query,
                                                                                        search_area_start,
                                                                                        BUFFER)

            query_limited: str = query[search_area_start:search_area_end]

            # getting best match indexes
            # and adding idx_search_start to them, because we limited the search area
            result = edlib.align(target, query_limited, task="path", mode="HW")

            similarity = 1 - result['editDistance'] / len(target)
            BUFFER += 5

            # print(similarity)
            ##print(search_area_start, search_area_end)
            ##print(query_limited)
            # print(target)
            # print()

            # time.sleep(5)

            if BUFFER > BUFFER_LIMIT:
                raise Exception('BUFFER is too big')

        best_match_start: int = search_area_start + result['locations'][0][0]
        best_match_end: int = search_area_start + result['locations'][0][-1]

        idx = 0

        for word in pdf_words:
            if best_match_start <= idx <= best_match_end:
                bbxs.append((word['page_no'], word['x0'], word['top'], word['x1'], word['bottom']))
            if idx >= best_match_end:
                break
            idx += len(word['text']) + 1

    return bbxs


def get_coordinates(pdf_words: list[dict], sentences_str: list[str]) -> list[
    tuple[int, float, float, float, float]]:
    bbxs: list[tuple[int, float, float, float, float]] = []

    # all words from pdf concatenated
    query: str = ' '.join([w['text'] for w in pdf_words])

    word_occurrences: dict = dict()
    search_from: int = 0

    while sentences_str:

        # sentence from xml that we want to find in the pdf
        target: str = sentences_str.pop(0)

        if target in word_occurrences:
            word_occurrences[target] += 1
        else:
            word_occurrences[target] = 0

        # adjust searching area while searching for the target sentence
        query_limited: str = query[search_from:]

        # getting best match indexes
        # and adding idx_search_start to them, because we limited the search area
        result = edlib.align(target, query_limited, task="path", mode="HW")

        similarity = max(1 - result['editDistance'] / len(target), 0)

        # i = word_occurrences.get(target, 0)
        # print(i)
        best_match_start = search_from + result['locations'][0][0]
        best_match_end = search_from + result['locations'][0][-1]
        #print(
        #    f'{target} -> {result["locations"]} -> {query[best_match_start:best_match_end]} -> {similarity}')
        #print()

        if similarity < 0.3:
            raise Exception('Similarity is too low')

        search_from = best_match_end

        # getting data for the bounding box for the target sentence
        idx = 0
        for word in pdf_words:
            if best_match_start <= idx <= best_match_end:
                bbxs.append((word['page_no'], word['x0'], word['top'], word['x1'], word['bottom']))
            if idx >= best_match_end:
                break
            idx += len(word['text']) + 1

    return bbxs


def main():
    # delete everything in the results folder
    shutil.rmtree('./results', ignore_errors=True)

    script_reader: ScriptReader = ScriptReader(
        './testing_xml',
        './testing_pdf',
    )

    SUCCESSFUL: int = 0
    UNSUCCESSFUL: int = 0

    for idx, (xml_file_path, pdf_file_path) in enumerate(script_reader.group_xml_pdf()):
        xml_editor: XMLEditor = XMLEditor(xml_file_path)

        # get a list of sentence elements from xml and convert them to list of strings
        sentences_ET: list[ET.Element] = xml_editor.get_elements_by_tags(SENTENCE_TAG)
        sentences_str1: list[str] = [get_text_from_element(sentence) for sentence in sentences_ET]
        sentences_str2: list[str] = [get_text_from_element(sentence) for sentence in sentences_ET]

        # get a list of all words in the pdf
        pdf_words1: list[dict] = get_words_from_pdf(pdf_file_path)
        pdf_words2: list[dict] = get_words_from_pdf(pdf_file_path)

        bbxs: list[tuple[int, float, float, float, float]] = []
        try:
            bbxs: list[tuple[int, float, float, float, float]] = get_coordinates(pdf_words1, sentences_str1)
            print(f'{idx}. WORKS ON: {pdf_file_path}')
            SUCCESSFUL += 1
        except Exception as e:
            print(f'{idx} TRYING HARDER ON: {pdf_file_path}')
            traceback.print_exc()
            try:
                bbxs: list[tuple[int, float, float, float, float]] = handle_exception(pdf_words2, sentences_str2)
                print(f'{idx}. WORKS ON: {pdf_file_path}')
                SUCCESSFUL += 1
            except Exception as e:
                print(f'{idx}. DOES NOT WORK ON: {pdf_file_path}')
                traceback.print_exc()
                UNSUCCESSFUL += 1

                # copy the pdf file to the exceptions folder
                shutil.copy(pdf_file_path, f'./exceptions/pdf/{os.path.basename(pdf_file_path)}')
                shutil.copy(pdf_file_path, f'./exceptions/xml/{os.path.basename(xml_file_path)}')
                continue

        # display the result
        prepare_result(xml_file_path, pdf_file_path, bbxs)

    # print the results
    print(f'SUCCESSFUL: {SUCCESSFUL}')
    print(f'UNSUCCESSFUL: {UNSUCCESSFUL}')
    print(f'%: {SUCCESSFUL / (SUCCESSFUL + UNSUCCESSFUL) * 100}')


if __name__ == '__main__':
    main()
