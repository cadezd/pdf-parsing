import os.path
import re
import shutil
import traceback
import xml.etree.ElementTree as ET

import edlib
import pdfplumber

from ScriptReader import ScriptReader
from XMLEditor import XMLEditor

# tags of sentence elements that contain text
SENTENCE_TAG: list[str] = ['s', 'note']
SENTENCE_TAG: list[str] = ['{http://www.tei-c.org/ns/1.0}' + tag for tag in SENTENCE_TAG]
# tags of word elements that contain text
WORD_TAG: list[str] = ['w', 'pc', 'note']
WORD_TAG: list[str] = ['{http://www.tei-c.org/ns/1.0}' + tag for tag in WORD_TAG]
# tags of elements that should be ignored (metadata)
NOTE_TAG: list[str] = ['note']
NOTE_TAG: list[str] = ['{http://www.tei-c.org/ns/1.0}' + tag for tag in NOTE_TAG]
# tags for segments
SEGMENT_TAG: list[str] = ['seg']
SEGMENT_TAG: list[str] = ['{http://www.tei-c.org/ns/1.0}' + tag for tag in SEGMENT_TAG]

CAHRS_THAT_INDICATE_NEW_LINE: set[str] = {'­', '-', ''}
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

SESSION_START_SLO: set = {"Začetek seje", "Seja se začne", "Seja sa začne", "Začetek ob ", "Seja se-začne",
                          "Soja se začne", "Seja se prične", "Seja še začne", "8eja se začne", "Seja 8p začne",
                          "Seja se začue", "Javna seja se začne", "Seja 86 začne o", "Seja se začnč o",
                          "®eJa se začne ob", "Seja se začnd o", "Seja sc začne o"}

SESSION_END_SLO: set = {"konec seje", "seja se konča", "seja prestane", "javna seja se konča", "seja se konta",
                        "seja se konca", "se konča o 45. minuti črez 2. uro", "seja se pretrga ol» 30. minuti čez",
                        "seja sc konča"}

SESSION_END_GER: set = {"schluß der sitzung", "schluss der sitzung", "schluß der öffentlichen sitzung",
                        "sdjluß der sitzung", "schluß !>er sitzung", "schlich brr sibling", "s njimi der sitzung",
                        "schluß der öffentlichen sitzung", "schluß irr sitzung", "schluß i rr sitzung",
                        "kchluß brr sihuiig", "ui der sitzung um 2 uhr",
                        "der sitzung um 12 uhr 15 minuten nachmittag",
                        "itfs der sitzung um 2 uhr 15 minuten nachmittag",
                        "ufs der sitzung um 2 uhr 30 minuten nachmittag", "zchluß der ätzung 1 uhr 15 minuten",
                        "der sitzung um 12 uhr 15 minuten uachiniltng", "schluß der kitznng", "der lihung",
                        "schluß iicr sitzung 11 uhr", "Schluß brv Sitzung", "Sd)lu6 hrr Sitzung"}

roman_numeros = {'I.', 'II.', 'III.', 'IV.', 'V.', 'VI.', 'VII.', 'VIII.', 'IX.', 'X.',
                 'XI.', 'XII.', 'XIII.', 'XIV.', 'XV.', 'XVI.', 'XVII.', 'XVIII.', 'XIX.', 'XX.',
                 'XXI.', 'XXII.', 'XXIII.', 'XXIV.', 'XXV.', 'XXVI.', 'XXVII.', 'XXVIII.', 'XXIX.', 'XXX.',
                 'XXXI.', 'XXXII.', 'XXXIII.', 'XXXIV.', 'XXXV.', 'XXXVI.', 'XXXVII.', 'XXXVIII.', 'XXXIX.', 'XL.'}

ADDIDIONAL_EQUALITIES: list[tuple[str, str]] = [
    ('m', 'n'), ('n', 'm'),
    ('>', 'i'),
    ('U', 'a'), ('a', 'U'),
    ('A', 'a'), ('a', 'A'),
    ('—', '-'), ('-', '—'),
]


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


def prepare_result(xml_path: str, pdf_path: str, bbxs: list[tuple[int, float, float, float, float]]):
    # create folder from the xml file name in the results folder
    file_name = os.path.basename(xml_path).split('.')[0]
    folder = os.path.join('results', file_name)
    os.makedirs(folder, exist_ok=True)

    images = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            images.append(page.to_image(resolution=150))

    for page_no, x1, y1, x2, y2 in bbxs:
        images[page_no].draw_rect((x1, y1, x2, y2), stroke_width=1)

    # save the images with the bounding boxes in the folder
    for idx, image in enumerate(images):
        image.save(os.path.join(folder, f'{file_name}_{idx}.png'))


def prepare_result1(xml_path: str, pdf_path: str) -> None:
    print('PREPARING RESULT for xml:', xml_path)
    xml_editor = XMLEditor(xml_path)
    elements_ET = xml_editor.get_elements_by_tags(WORD_TAG)

    # create folder from the xml file name in the results folder
    file_name = os.path.basename(xml_path).split('.')[0]
    folder = os.path.join('results', file_name)
    os.makedirs(folder, exist_ok=True)

    images = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            images.append(page.to_image(resolution=150))

    for element in elements_ET:
        try:
            if 'x0' not in element.attrib:
                continue

            fromPage = int(element.attrib['fromPage'])
            toPage = int(element.attrib['toPage'])

            for i, j in zip(range(0, 10, 2), range(1, 11, 2)):
                if f'x{i}' not in element.attrib or f'y{i}' not in element.attrib:
                    break

                if f'x{j}' not in element.attrib or f'y{j}' not in element.attrib:
                    break

                x0 = float(element.attrib[f'x{i}'])
                y0 = float(element.attrib[f'y{i}'])
                x1 = float(element.attrib[f'x{j}'])
                y1 = float(element.attrib[f'y{j}'])

                page_num = fromPage if i <= 0 and j <= 1 else toPage

                images[page_num].draw_rect((
                    x0,
                    y0,
                    x1,
                    y1,
                ), stroke_width=1)


        except Exception as e:
            print('Problem with:', element.text)
            continue

    # save the images with the bounding boxes in the folder
    for idx, image in enumerate(images):
        image.save(os.path.join(folder, f'{file_name}_{idx}.png'))


def get_chars_from_pdf(pdf_path: str, start_of_session: str, end_of_session: str) -> list[dict]:
    # list that will store all words in the pdf
    all_pdf_chars: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        # iterating through pages and getting all words on each page
        for page_no, pdf_page in enumerate(pdf.pages):
            # get all chars on the page
            page_chars: list[dict] = pdf_page.chars

            # skipping pages with no chars
            if not page_chars:
                continue

            # add words from the page to the list of all words in the pdf
            all_pdf_chars.extend(page_chars)

    # join all chars in the pdf to get the query string
    query: str = ''.join([c['text'] for c in all_pdf_chars])

    # get index of words that indicate the start of the session content
    results_start: dict = edlib.align(
        start_of_session,
        query,
        task="path",
        mode="HW",
        additionalEqualities=ADDIDIONAL_EQUALITIES
    )
    idx_from: int = results_start['locations'][0][-1]
    first_page = all_pdf_chars[idx_from]['page_number']
    bottom = all_pdf_chars[idx_from]['bottom']

    # get index of words that indicate the start of the session content
    results_end: dict = edlib.align(
        end_of_session,
        query,
        task="path",
        mode="HW",
        additionalEqualities=ADDIDIONAL_EQUALITIES
    )
    idx_to: int = results_end['locations'][-1][-1]
    last_page = all_pdf_chars[idx_to]['page_number']

    # get only the words that are part of the session content
    all_pdf_chars = [char for char in all_pdf_chars if (char['page_number'] > first_page) or (
            char['page_number'] == first_page and char['bottom'] > bottom)]
    all_pdf_chars = [char for char in all_pdf_chars if char['page_number'] <= last_page]
    # remove spaces from the chars (better alignment and search)
    all_pdf_chars = [char for char in all_pdf_chars if not char['text'].isspace()]

    return all_pdf_chars


def is_valid(words: list[ET.Element], percentage: float) -> bool:
    num_of_words_with_coords = 0
    for word in words:
        if 'x0' in word.attrib and 'y0' in word.attrib and 'x1' in word.attrib and 'y1' in word.attrib:
            num_of_words_with_coords += 1

    return num_of_words_with_coords / len(words) >= percentage


def get_start_and_end_note(notes_ET: list[ET.Element]) -> tuple[str, str]:
    notes_str: list[str] = [get_text_from_element(note) for note in notes_ET]

    # we get last note which is hopefully on the last page
    # we use them to get rid of the noise at the end of the pdf, but keep the words
    # on the last page that are part of the session content
    session_end_note: str = notes_str[-1]

    # notes that have type time and are in German
    notes_ET_time = list(
        filter(lambda n: 'type' in n.attrib and n.attrib['type'] == 'time' and \
                         '{http://www.w3.org/XML/1998/namespace}lang' in n.attrib and \
                         n.attrib['{http://www.w3.org/XML/1998/namespace}lang'] == 'de',
               notes_ET)
    )

    notes_str_time: list[str] = [get_text_from_element(note) for note in notes_ET_time]

    # get GER note that indicates beginning of the session content
    # we always select the GER one because after the GER note there is always session content
    session_start_note: str = notes_str_time[0] if notes_str_time else notes_str[0]

    return session_start_note, session_end_note


def add_coordinates_to_xml(pdf_chars: list[dict], sentence: ET.Element):
    # get xml elements (words and punctuations) from sentence element
    elements_in_sentence: list[ET.Element] = [child for child in sentence]

    query: str = ''.join([char['text'] for char in pdf_chars])
    query = re.sub(r'\s+', '', query)

    # limit_search: bool = any([c in CAHRS_THAT_INDICATE_NEW_LINE for c in query]) or \
    #                     any([abs(c['bottom'] - pdf_chars[i + 1]['bottom']) >= 300 for i, c in
    #                          enumerate(pdf_chars[:-1])])

    best_match_end: int = 0
    result = None

    # print("QUERY:", query)
    # is_first: bool = True
    search_from: int = 0
    while elements_in_sentence:
        # get element from the sentence and get the target text
        element: ET.Element = elements_in_sentence.pop(0)
        target: str = re.sub(r'\s+', '', element.text)

        similarity_curr: float = 0
        similarity_prev: float = -1
        BUFFER: int = 5

        while similarity_prev < similarity_curr < 1.0:
            search_area_start = best_match_end
            search_area_end = search_area_start + len(target) + BUFFER

            # if limit_search:
            #    if is_first:
            #        search_area_end = search_area_start + len(target)
            #    query_limited: str = query[search_area_start:search_area_end]
            #    is_first = False
            # else:
            #    query_limited: str = query[search_area_start:]

            query_limited: str = query[search_area_start:search_area_end]

            # getting best match indexes
            # and adding idx_search_start to them, because we limited the search area
            result = edlib.align(
                target,
                query_limited,
                task="path",
                mode='HW',
                additionalEqualities=ADDIDIONAL_EQUALITIES
            )

            similarity_prev = similarity_curr
            similarity_curr = 1 - result['editDistance'] / len(target)

            BUFFER += 2

        locations = result['locations']
        if result['locations'][0][0] is None:
            continue

        best_match_start = search_from + locations[0][0]
        best_match_end = search_from + locations[0][-1]

        similarity = 1 - result['editDistance'] / len(target)

        # print('TARGET:', target, '|', 'BEST MATCH:', query[best_match_start: best_match_end + 1], '|', 'SIMILARITY:',
        #      similarity, '|', 'SEARCH FROM:', search_from, '|', 'BEST MATCH END:', best_match_end)

        search_from = best_match_end if best_match_end > search_from or \
                                        (elements_in_sentence and len(
                                            elements_in_sentence[0].text) > 1) else best_match_end + 1

        # get coordinates for target text and add them to the xml element
        coord_counter: int = 0
        for i, char in enumerate(pdf_chars):
            if i == best_match_start:
                element.set(f'x{coord_counter}', str(round(char['x0'], 2)))
                element.set(f'y{coord_counter}', str(round(char['top'], 2)))
                element.set('fromPage', str(char['page_number'] - 1))
                element.set('isBroken', 'false')
                coord_counter += 1

            if best_match_end - best_match_start > 1 and \
                    best_match_start <= i < best_match_end and \
                    i + 1 < len(pdf_chars) and \
                    abs(int(char['bottom']) - int(pdf_chars[i + 1]['bottom'])) >= 4:
                # end of previous part of the word
                element.set(f'x{coord_counter}', str(round(char['x1'], 2)))
                element.set(f'y{coord_counter}', str(round(char['bottom'], 2)))
                coord_counter += 1
                # start of new part of the word
                element.set(f'x{coord_counter}', str(round(pdf_chars[i + 1]['x0'], 2)))
                element.set(f'y{coord_counter}', str(round(pdf_chars[i + 1]['top'], 2)))
                coord_counter += 1

                element.set('isBroken', 'true')

            if i == best_match_end:
                element.set(f'x{coord_counter}', str(round(char['x1'], 2)))
                element.set(f'y{coord_counter}', str(round(char['bottom'], 2)))
                element.set('toPage', str(char['page_number'] - 1))

            if i > best_match_end:
                break

    # print()


def remove_pdf_chars(pdf_chars: list[dict], positions: list[tuple[int, int]]) -> list[dict]:
    # removes chars from idx_start to idx_end
    # print('\nREMOVING TITLES:')
    new_pdf_chars: list[dict] = []
    w = ''
    for i, char in enumerate(pdf_chars):
        if any([position[0] <= i < position[1] for position in positions]):
            w += char['text']
        else:
            if w:
                # print(w)
                w = ''
            new_pdf_chars.append(char)

    return new_pdf_chars


def get_bbxs(pdf_chars: list[dict], idx_start: int, idx_end: int) -> list[tuple[int, float, float, float, float]]:
    # getting data for the bounding box for the target sentence
    bbxs: list[tuple[int, float, float, float, float]] = []
    for i, char in enumerate(pdf_chars):
        if idx_start <= i <= idx_end:
            page_no = char['page_number']
            x0 = round(char['x0'], 2)
            y0 = round(char['top'], 2)
            x1 = round(char['x1'], 2)
            y1 = round(char['bottom'], 2)
            bbxs.append((page_no - 1, x0, y0, x1, y1))

        if i >= idx_end:
            break

    return bbxs


def search_for_words_limited(pdf_chars: list[dict], elements_ET: list[ET.Element]):
    query: str = '@' + ''.join([char['text'] for char in pdf_chars])
    query = re.sub(r'\s+', '', query)

    is_first: bool = True
    result = None
    best_match_end: int = 0
    search_area_start: int = 0

    while elements_ET:
        # get element as string
        element_ET: ET.Element = elements_ET.pop(0)
        target: str = get_text_from_element(element_ET)
        target = re.sub(r'\s+', '', target)

        similarity_curr: float = 0
        similarity_prev: float = -1
        BUFFER: int = 5

        while similarity_prev < similarity_curr < 1.0:
            # adjust searching area while searching for the target sentence
            search_area_start = best_match_end
            search_area_end = search_area_start + len(target) + BUFFER

            query_limited: str = query[search_area_start:search_area_end]

            # getting best match indexes
            # and adding idx_search_start to them, because we limited the search area
            result = edlib.align(
                target,
                query_limited,
                task="path",
                mode='HW',
                additionalEqualities=ADDIDIONAL_EQUALITIES
            )

            similarity_prev = similarity_curr
            similarity_curr = 1 - result['editDistance'] / len(target)
            BUFFER += 3

            # print(similarity_curr)
            # print(search_area_start, search_area_end)
            # print('QUERY:', query_limited)
        # print('TARGER:', target)
        # print('TAG:', element_ET.tag)
        # print()

        # print(target)
        # print(similarity_curr)
        # print()

        if result['locations'][0][0] is None:
            continue

        best_match_start: int = search_area_start + result['locations'][0][0]
        best_match_end: int = search_area_start + result['locations'][0][-1]

        if 'note' not in element_ET.tag:
            add_coordinates_to_xml(pdf_chars[best_match_start - 1:best_match_end + 1], element_ET)

        # stop when reaching the end of the session content
        if best_match_end == len(query) - 1:
            break

        query = query.replace('@', '')


def search_for_words_all(pdf_words: list[dict], sentences_ET: list[ET.Element]) -> \
        list[tuple[int, float, float, float, float]]:
    bbxs: list[tuple[int, float, float, float, float]] = []

    # all words from pdf concatenated
    query: str = ' '.join([w['text'] for w in pdf_words])

    search_from: int = 0

    while sentences_ET:

        # get sentence as string from the sentence element
        sentence_ET = sentences_ET.pop(0)
        # remove titles that are not part of the sentence
        target: str = get_text_from_element(sentence_ET)

        # adjust searching area while searching for the target sentence
        query_limited: str = query[search_from:]

        # getting best match indexes
        # and adding idx_search_start to them, because we limited the search area
        result = edlib.align(target, query_limited, task="path", mode="HW")

        if len(target) == 0:
            continue

        similarity = max(1 - result['editDistance'] / len(target), 0)

        # i = word_occurrences.get(target, 0)
        # print(i)
        locations = result['locations']
        best_match_start = search_from + locations[0][0]
        best_match_end = search_from + locations[0][-1] + 1

        # print(target)
        # print(similarity)
        # print(search_from)
        # print()

        if similarity < 0.3:
            # print(similarity)
            raise Exception('Similarity is too low')

        search_from = best_match_end

        if 'note' not in sentence_ET.tag:
            bbxs.extend(get_bbxs(pdf_words, best_match_start, best_match_end))

        # stop when reaching the end of the session content
        if best_match_end == len(query) - 1:
            break

    return bbxs


def get_locations_to_remove(s: str, min_length: int) -> list[tuple[int, int]]:
    """
    This function gets the locations of the matched words in the alignment.

    :param min_length:
    :param s:
    :return:
    """
    sequences = []
    start = None  # To mark the start of a sequence of '-'
    noise_count = 0  # To count the '|' characters within a sequence

    for i, char in enumerate(s):
        if char == '-':
            if start is None:
                start = i  # Mark the start of a sequence
                noise_count = 0  # Reset noise count
        else:
            if start is not None:
                noise_count += 1  # Increment noise count

                if all([c != '-' for c in s[i + 1:i + 1 + 5]]):
                    if (i - noise_count) - start >= min_length:
                        sequences.append((start, i - noise_count + 1))  # End of a sequence
                    start = None

    if start is not None and (len(s) - noise_count) - start >= min_length:
        sequences.append((start, len(s)))

    return sequences


def align(pdf_chars: list[dict], elements_ET: list[ET.Element], min_length: int) -> list[dict]:
    """
    Purpose of this function is to make texts from pdf and xml as similar as possible by removing
    any text from the pdf that is not in the xml, therefore making the alignment of the texts easier.

    :param pdf_chars:
    :param elements_ET:
    :return:
    """

    target: str = ''.join([get_text_from_element(element_ET) for element_ET in elements_ET])
    target = re.sub(r'\s+', '', target)

    # all words from pdf concatenated into  query
    query: str = ''.join([w['text'] for w in pdf_chars])
    query = re.sub(r'\s+', '', query)

    result = edlib.align(target, query, task="path", mode="NW")
    nice = edlib.getNiceAlignment(result, target, query)

    # remove the chars from the pdf that are not in the xml based on the locations
    locations = get_locations_to_remove(nice['matched_aligned'], min_length)
    pdf_chars = remove_pdf_chars(pdf_chars, locations)

    # print(len(target), len(query), len(nice['matched_aligned']))

    return pdf_chars


def main():
    # delete everything in the results folder
    # shutil.rmtree('./results', ignore_errors=True)

    script_reader: ScriptReader = ScriptReader(
        './all_xml',
        './all_pdf',
        # _idx=0
        _from=382 + 247
        # _from=70,
        # _to=100
    )

    SUCCESSFUL: int = 0
    UNSUCCESSFUL: int = 0

    for idx, (xml_file_path, pdf_file_path) in enumerate(script_reader.group_xml_pdf()):
        xml_editor: XMLEditor = XMLEditor(xml_file_path)

        print(f'PROCESSING: {pdf_file_path}')

        # get a list of note elements from xml
        notes_ET: list[ET.Element] = xml_editor.get_elements_by_tags(NOTE_TAG)
        # get session start and end notes (to remove header and noise at the end)
        session_start_note, session_end_note = get_start_and_end_note(notes_ET)
        session_start_note = re.sub(r'\s+', '', session_start_note)
        session_end_note = re.sub(r'\s+', '', session_end_note)

        # kepp only et elements that are after first ger time note
        sentences_ET: list[ET.Element] = xml_editor.get_elements_by_tags(SENTENCE_TAG)

        # remove first n notes
        i_from = 0
        for i, sentence_ET in enumerate(sentences_ET):
            if 'note' not in sentence_ET.tag:
                i_from = i
                break

        sentences_ET = sentences_ET[i_from:]

        # get all chars from the pdf
        pdf_chars = align(
            get_chars_from_pdf(pdf_file_path, session_start_note, session_end_note), sentences_ET,
            0
        )

        try:
            search_for_words_limited(pdf_chars, sentences_ET)

            words = xml_editor.get_elements_by_tags(WORD_TAG)
            words = [word for word in words if word.tag not in NOTE_TAG]
            if not is_valid(words, 0.85):
                raise Exception('Not valid')

            print(f'{idx}. WORKS ON: {pdf_file_path}')

            # display the result
            xml_editor.save(f'./output')
            # get the base name of the xml file
            file_name = os.path.basename(xml_file_path)
            prepare_result1(f'./output/{file_name}', pdf_file_path)

            SUCCESSFUL += 1

        except Exception as e:

            print(f'{idx}. DOES NOT WORK ON: {pdf_file_path}')
            traceback.print_exc()
            UNSUCCESSFUL += 1

            # copy the pdf file to the exceptions_test folder
            shutil.copy(pdf_file_path, f'exceptions/pdf/{os.path.basename(pdf_file_path)}')
            shutil.copy(xml_file_path, f'exceptions/xml/{os.path.basename(xml_file_path)}')
            continue

    # print the results
    print(f'SUCCESSFUL: {SUCCESSFUL}')
    print(f'UNSUCCESSFUL: {UNSUCCESSFUL}')
    print(f'%: {SUCCESSFUL / (SUCCESSFUL + UNSUCCESSFUL) * 100}')


if __name__ == '__main__':
    main()
