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
WORD_TAG: list[str] = ['w', 'pc']
WORD_TAG: list[str] = ['{http://www.tei-c.org/ns/1.0}' + tag for tag in WORD_TAG]
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
        if 'x0' not in element.attrib:
            continue

        x0 = float(element.attrib['x0'])
        y0 = float(element.attrib['y0'])
        x1 = float(element.attrib['x1'])
        y1 = float(element.attrib['y1'])
        fromPage = int(element.attrib['fromPage'])

        images[fromPage].draw_rect((x0, y0, x1, y1), stroke_width=1)

        isBroken: bool = element.attrib['isBroken'] == 'true'
        if isBroken:
            toPage = int(element.attrib['toPage'])
            x2 = float(element.attrib['x2'])
            y2 = float(element.attrib['y2'])
            x3 = float(element.attrib['x3'])
            y3 = float(element.attrib['y3'])

            images[toPage].draw_rect((x2, y2, x3, y3), stroke_width=1)

    # save the images with the bounding boxes in the folder
    for idx, image in enumerate(images):
        image.save(os.path.join(folder, f'{file_name}_{idx}.png'))


def get_words_from_pdf(pdf_path: str, start_of_session: str, end_of_session: str, remove_titles: bool = False) -> \
        tuple[list[dict], list[str]]:
    # list that will store all words in the pdf
    all_pdf_words: list[dict] = []
    pdf_words_excluded: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        # iterating through pages and getting all words on each page
        for page_no, pdf_page in enumerate(pdf.pages):
            # get all words based on PDF's underlying flow of characters
            page_words: list[dict] = pdf_page.extract_words(use_text_flow=True, x_tolerance=10)

            # skipping pages with no words
            if not page_words:
                continue

            # adding page no to each word
            page_words = [{'page_no': page_no, **word} for word in page_words]

            page_words_wanted = []
            page_words_excluded = []

            # save title at the top of the page
            words = [w['text'].strip() for w in page_words]
            text = ' '.join([w['text'].strip() for w in page_words])
            first_word = page_words[0]
            second_word = page_words[1] if len(page_words) > 1 else None

            for n in roman_numeros:
                if n in first_word['text'] or (second_word and n in second_word['text']):
                    rest_of_text = text.strip()[text.strip().find(n) + len(n):].lower().replace(' ', '')
                    if len(words) > 4 and n in words[4:]:
                        # keep only words that have top coordinate lower that bottom coordinate of first word
                        page_words_excluded = ' '.join(
                            [w['text'] for w in page_words if w['top'] <= first_word['bottom']])

                    if "sitzungun" in rest_of_text or "sejadne" in rest_of_text or "sitzungam" in rest_of_text or "sitzungmn" in rest_of_text or "sitzungant" in rest_of_text or "sitzungnm" in rest_of_text:
                        # keep only words that have top coordinate lower that bottom coordinate of first word
                        page_words_excluded = ' '.join(
                            [w['text'] for w in page_words if w['top'] <= first_word['bottom']])

                    part2 = text.strip().split(chr(8212))  # U+8212 je Em Dash (pomišljaj)
                    if len(part2) > 1 and part2[1].strip().startswith(n):
                        # keep only words that have top coordinate lower that bottom coordinate of first word
                        page_words_excluded = ' '.join(
                            [w['text'] for w in page_words if w['top'] <= first_word['bottom']])

            all_pdf_words.extend(page_words)
            if page_words_excluded:
                pdf_words_excluded.append(page_words_excluded)

    # make query
    query: str = ' '.join([w['text'] for w in all_pdf_words])

    # get index of the start of the session
    results_start: dict = edlib.align(start_of_session, query, task="path", mode="HW")
    idx_from: int = results_start['locations'][0][-1]

    results_end: dict = edlib.align(end_of_session, query, task="path", mode="HW")
    idx_to: int = results_end['locations'][-1][-1]

    # get the last page of the session content
    idx: int = 0
    last_page_of_content: int = 0
    for word in all_pdf_words:
        if idx_from <= idx <= idx_to:
            last_page_of_content = word['page_no']
        idx += len(word['text']) + 1

    # filter words that are between the start and the end of the session
    # to remove the header at the start of the pdf and noise at the end of the pdf
    pdf_words_wanted: list = []
    idx: int = 0
    for word in all_pdf_words:
        if idx_from <= idx <= idx_to or last_page_of_content == word['page_no']:
            last_page_of_content = word['page_no']
            pdf_words_wanted.append(word)

        idx += len(word['text']) + 1

    return pdf_words_wanted, pdf_words_excluded


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


def is_last_sentence(sentence: str):
    # check if the sentence is the last one (to avoid noise in the pdf)
    for key_word_session_end in SESSION_END_GER:
        if key_word_session_end.lower() in sentence.lower():
            return True

    return False


def remove_excluded_words(sentence: str, excluded_words: list[str]) -> str:
    PATTERN_REMOVE_PAGE_NUMBERS = r'\b\d{3}\b'
    PATTERN_REMOVE_UNNECESSARY_SPACES = r'\s{2,}'

    sentence = sentence.replace('—', '')
    sentence = sentence.strip()

    for excluded_word in excluded_words:
        if type(excluded_word) == list:
            continue

        slo_excluded_words = excluded_word.split('—')[0]
        slo_excluded_words = re.sub(PATTERN_REMOVE_PAGE_NUMBERS, '', slo_excluded_words)
        slo_excluded_words = re.sub(PATTERN_REMOVE_UNNECESSARY_SPACES, '', slo_excluded_words)
        slo_excluded_words = slo_excluded_words.replace('.', '\.')
        slo_excluded_words = slo_excluded_words.strip()

        ger_excluded_words = excluded_word.split('—')[-1]
        ger_excluded_words = re.sub(PATTERN_REMOVE_PAGE_NUMBERS, '', ger_excluded_words)
        ger_excluded_words = re.sub(PATTERN_REMOVE_UNNECESSARY_SPACES, '', ger_excluded_words)
        ger_excluded_words = re.sub(r'm|n', '[m|n]', ger_excluded_words)
        ger_excluded_words = ger_excluded_words.replace('.', '\.')
        ger_excluded_words = ger_excluded_words.strip()

        if re.search(slo_excluded_words, sentence):
            sentence = re.sub(slo_excluded_words, '', sentence)

        if re.search(ger_excluded_words, sentence):
            sentence = re.sub(ger_excluded_words, '', sentence)

    return sentence


def contains_excluded_words(query: str, regex_patterns_excluded_words: list[str]) -> bool:
    for pattern in regex_patterns_excluded_words:
        try:
            if re.search(pattern, query):
                return True
        except:
            print(f'Error in regex pattern {pattern}')
            continue

    return False


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def get_match_positions(query: str, regex_patterns_excluded_words: list[str]) -> tuple[int, int]:
    for pattern in regex_patterns_excluded_words:
        match = re.search(pattern, query)
        if match:
            return match.start(), match.end()

    return -1, -1


def make_regex_for_excluded_words(excluded_words: list[str]) -> tuple[list[str], list[str], list[str]]:
    patterns_full: list[str] = []
    patterns_slo: list[str] = []
    patterns_ger: list[str] = []

    for excluded_word in excluded_words:

        full_excluded_words_pattern = excluded_word.strip()
        full_excluded_words_pattern = full_excluded_words_pattern.replace('.', r'\.')
        if '-' in full_excluded_words_pattern:
            full_excluded_words_pattern = full_excluded_words_pattern.replace('-', r'(-|—)?')
        elif '—' in full_excluded_words_pattern:
            full_excluded_words_pattern = full_excluded_words_pattern.replace('—', r'(-|—)?')
        full_excluded_words_pattern = full_excluded_words_pattern.replace('am', r'a(m|n)')
        full_excluded_words_pattern = full_excluded_words_pattern.replace('ant', r'a(m|n)t?')
        full_excluded_words_pattern = re.sub(r'\s+', ' ', full_excluded_words_pattern)
        full_excluded_words_pattern = full_excluded_words_pattern.replace(' ', r'\s+')

        slo_excluded_words = ' '.join(excluded_word.split(' ')[:7]).strip()
        slo_excluded_words = slo_excluded_words.replace('.', r'\.')
        slo_excluded_words = re.sub(r'\s+', ' ', slo_excluded_words)
        slo_excluded_words = slo_excluded_words.replace(' ', r'\s+')

        ger_excluded_words = ' '.join(excluded_word.split(' ')[7:]).strip()
        ger_excluded_words = ger_excluded_words.replace('am', r'a(m|n)')
        ger_excluded_words = ger_excluded_words.replace('ant', r'a(m|n)t?')
        ger_excluded_words = ger_excluded_words.replace('.', r'\.')
        ger_excluded_words = re.sub(r'\s+', ' ', ger_excluded_words)
        ger_excluded_words = ger_excluded_words.replace(' ', r'\s+')

        patterns_full.append(full_excluded_words_pattern)
        patterns_slo.append(slo_excluded_words)
        patterns_ger.append(ger_excluded_words)

    return patterns_full, patterns_slo, patterns_ger


def make_regex_for_excluded_words1(excluded_words: list[str]) -> tuple[list[str], list[str], list[str]]:
    patterns: list[str] = []
    patterns_slo: list[str] = []
    patterns_ger: list[str] = []

    for i, excluded_word in enumerate(excluded_words):

        if '—' in excluded_word and len(excluded_word.strip().split('—')) >= 2:
            words = excluded_word.split(' ')
            pattern = ' '.join(words[:2]).replace('.', r'\.') + r'.+' + \
                      ' '.join(words[-3:]).replace('.', r'\.?')

            front_words = excluded_word.split('—')[0].strip().split(' ')
            back_words = excluded_word.split('—')[-1].strip().split(' ')
            pattern_slo = ' '.join(front_words[:2]).replace('.', r'\.') + r'.+' + ' '.join(front_words[-3:]).replace(
                '.', r'\.?')
            pattern_ger = ' '.join(back_words[:2]).replace('.', r'\.') + r'.+' + \
                          ' '.join(back_words[-3:]).replace('.', r'\.?')

            pattern_ger = rreplace(pattern_ger, r'\.? ', r'\.?|', 1)

            patterns.append(pattern)
            patterns_slo.append(pattern_slo)
            patterns_ger.append(pattern_ger)

        elif '-' in excluded_word and len(excluded_word.strip().split('-')) >= 2:
            words = excluded_word.split(' ')
            pattern = ' '.join(words[:2]).replace('.', r'\.') + r'.+' + \
                      ' '.join(words[-3:]).replace('.', r'\.?')

            front_words = excluded_word.split('-')[0].strip().split(' ')
            back_words = excluded_word.split('-')[-1].strip().split(' ')
            pattern_slo = ' '.join(front_words[:2]).replace('.', r'\.') + r'.+' + ' '.join(front_words[-3:]).replace(
                '.', r'\.?')
            pattern_ger = ' '.join(back_words[:2]).replace('.', r'\.') + r'.+' + \
                          ' '.join(back_words[-3:]).replace('.', r'\.?')

            pattern_ger = rreplace(pattern_ger, r'\.? ', r'\.?|', 1)

            patterns.append(pattern)
            patterns_slo.append(pattern_slo)
            patterns_ger.append(pattern_ger)

        else:
            words = excluded_word.split(' ')
            pattern = ' '.join(words[:2]).replace('.', r'\.') + r'.+' + \
                      ' '.join(words[-3:]).replace('.', r'\.?')

            pattern = rreplace(pattern, r'\.? ', r'\.?|', 1)

            patterns.append(pattern)

            # get me the idx of 3 digit number
            match = re.search(r'\b\d{1,3}\b', excluded_word)
            i_start = match.start()
            if i_start >= 7:
                back_words = excluded_word[6:].split(' ')
                pattern_ger = ' '.join(back_words[:2]).replace('.', r'\.') + r'.+' + \
                              ' '.join(back_words[-3:]).replace('.', r'\.?')

                pattern_ger = rreplace(pattern_ger, r'\.? ', r'\.?|', 1)

                patterns_ger.append(pattern_ger)

    return patterns, patterns_slo, patterns_ger


def add_coordinates_to_xml(idx_start: int, idx_end: int, pdf_words: list[dict], sentence: ET.Element,
                           has_title: bool = False):
    # get xml elements (words and punctuations) from sentence element
    elements_in_sentence: list[ET.Element] = [child for child in sentence]

    # get data about words from the pdf
    mathing_words: list[dict] = []
    idx: int = 0
    for word in pdf_words:
        if idx_start <= idx <= idx_end:
            mathing_words.append(word)
        if idx > idx_end:
            break
        idx += len(word['text']) + 1

    # add coordinate to the xml element
    query: str = ' '.join([w['text'] for w in mathing_words])

    best_match_end: int = 0

    result = {'locations': []}

    # check if any of the words in the sentence can be a title based on the top coordinate
    if has_title:
        can_have_title: bool = any([True if word['top'] <= 150 else False for word in mathing_words])
    else:
        can_have_title: bool = False

    print("QUERY:", query)

    search_from: int = 0
    while elements_in_sentence:
        # get element from the sentence and get the target text
        element: ET.Element = elements_in_sentence.pop(0)
        target: str = element.text

        similarity_curr: float = 0
        similarity_prev: float = -1
        BUFFER: int = 0

        while similarity_prev < similarity_curr:
            search_area_start = best_match_end
            search_area_end = search_area_start + len(target) + BUFFER

            query_limited: str = query[search_area_start:search_area_end]

            # getting best match indexes
            # and adding idx_search_start to them, because we limited the search area
            result = edlib.align(target, query_limited, task="path", mode='HW')

            similarity_prev = similarity_curr
            similarity_curr = 1 - result['editDistance'] / len(target)

            if not can_have_title:
                BUFFER += 4
            else:
                BUFFER += 10

        if result['locations'][0][0] == None or result['locations'][0] == (0, -1):
            continue

        locations = result['locations']
        best_match_start = search_from + locations[0][0]
        best_match_end = search_from + locations[0][-1] + 1

        similarity = 1 - result['editDistance'] / len(target)

        print('TARGET:', target, '|', 'BEST MATCH:', query[best_match_start: best_match_end], '|', 'SIMILARITY:',
              similarity)

        search_from = best_match_end

        # get coordinates for target text and add them to the xml element
        idx: int = 0
        for word in mathing_words:
            if best_match_start <= idx <= best_match_end and 'isBroken' not in element.attrib:
                element.set('x0', str(round(word['x0'], 2)))
                element.set('y0', str(round(word['top'], 2)))
                element.set('x1', str(round(word['x1'], 2)))
                element.set('y1', str(round(word['bottom'], 2)))
                element.set('fromPage', str(word['page_no']))
                element.set('toPage', str(word['page_no']))
                element.set('isBroken', 'false')
            elif best_match_start <= idx <= best_match_end and 'isBroken' in element.attrib:
                element.set('x2', str(round(word['x0'], 2)))
                element.set('y2', str(round(word['top'], 2)))
                element.set('x3', str(round(word['x1'], 2)))
                element.set('y3', str(round(word['bottom'], 2)))
                element.set('toPage', str(word['page_no']))
                element.set('isBroken', 'true')

            if idx > best_match_end:
                break

            idx += len(word['text']) + 1

    print()


def remove_from_pdf_words(pdf_words: list[dict], idx_start: int, idx_end: int) -> list[dict]:
    # removes words from idx_start to idx_end
    new_pdf_words: list[dict] = []
    idx: int = 0
    for i, word in enumerate(pdf_words):
        if idx_start <= idx <= idx_end:
            # print(word['text'])
            ...
        else:
            new_pdf_words.append(word)

        idx += len(word['text']) + 1

    # print()

    return new_pdf_words


def get_bbxs(pdf_words: list[dict], idx_start: int, idx_end: int) -> list[tuple[int, float, float, float, float]]:
    # getting data for the bounding box for the target sentence
    bbxs: list[tuple[int, float, float, float, float]] = []
    idx = 0
    for word in pdf_words:
        if idx_start <= idx <= idx_end:
            page_no = word['page_no']
            x0 = round(word['x0'], 2)
            y0 = round(word['top'], 2)
            x1 = round(word['x1'], 2)
            y1 = round(word['bottom'], 2)
            bbxs.append((page_no, x0, y0, x1, y1))
        if idx > idx_end:
            break
        idx += len(word['text']) + 1

    return bbxs


def remove_titles(pdf_words: list[dict], sentences_ET: list[ET.Element], regex_patterns_excluded_words: list[str]) -> \
        list[dict]:
    query: str = ' '.join([w['text'] for w in pdf_words])

    best_match_end: int = 0

    result = {'locations': []}
    search_area_start: int = 0

    while sentences_ET:
        # get sentence as string from the sentence element
        target: str = get_text_from_element(sentences_ET.pop(0))

        # handle titles that are broken into 2 sentences

        similarity_curr: float = 0
        similarity_prev: float = -1
        BUFFER: int = 4

        while similarity_prev < similarity_curr:
            # adjust searching area while searching for the target sentence
            search_area_start = best_match_end
            search_area_end = search_area_start + len(target) + get_len_of_next_n_words(query,
                                                                                        search_area_start,
                                                                                        BUFFER)

            query_limited: str = query[search_area_start:search_area_end]

            # print('QUERY:', query_limited)
            # print('TARGET:', target)
            # print()

            if contains_excluded_words(query_limited, regex_patterns_excluded_words) and \
                    not contains_excluded_words(target, regex_patterns_excluded_words):
                start_excluded, end_excluded = get_match_positions(query_limited,
                                                                   regex_patterns_excluded_words)

                pdf_words = remove_from_pdf_words(pdf_words, search_area_start + start_excluded,
                                                  search_area_start + end_excluded)

                query = ' '.join([w['text'] for w in pdf_words])

                query_limited: str = query[search_area_start:search_area_end]

            # getting best match indexes
            # and adding idx_search_start to them, because we limited the search area
            result = edlib.align(target, query_limited, task="path", mode='HW')

            similarity_prev = similarity_curr
            similarity_curr = 1 - result['editDistance'] / len(target)

        best_match_end: int = search_area_start + result['locations'][0][-1] + 1

        # stop when reaching the end of the session content
        if best_match_end == len(query) - 1:
            break

    return pdf_words


def search_for_words_limited(pdf_words: list[dict], elements_ET: list[ET.Element]) -> \
        list[tuple[int, float, float, float, float]]:
    bbxs: list[tuple[int, float, float, float, float]] = []

    query: str = ' '.join([w['text'] for w in pdf_words])

    best_match_start: int = 0
    best_match_end: int = 0

    result = {'locations': []}
    search_area_start: int = 0

    while elements_ET:
        # get element as string
        element_ET: ET.Element = elements_ET.pop(0)
        target: str = get_text_from_element(element_ET)

        similarity_curr: float = 0
        similarity_prev: float = -1
        BUFFER: int = 3

        while similarity_prev < similarity_curr:
            # adjust searching area while searching for the target sentence
            search_area_start = best_match_end
            search_area_end = search_area_start + len(target) + get_len_of_next_n_words(query,
                                                                                        search_area_start,
                                                                                        BUFFER)

            query_limited: str = query[search_area_start:search_area_end]

            # getting best match indexes
            # and adding idx_search_start to them, because we limited the search area
            result = edlib.align(target, query_limited, task="path", mode='HW')

            similarity_prev = similarity_curr
            similarity_curr = 1 - result['editDistance'] / len(target)
            BUFFER += 1

            # print(similarity_curr)
            # print(search_area_start, search_area_end)
            # print(query_limited)
            # print(target)
            # print()

        # print(target)
        # print(similarity_curr)
        # print()

        best_match_start: int = search_area_start + result['locations'][0][0]
        best_match_end: int = search_area_start + result['locations'][0][-1]

        if element_ET.tag != '{http://www.tei-c.org/ns/1.0}note':
            bbxs.extend(get_bbxs(pdf_words, best_match_start, best_match_end))

        # stop when reaching the end of the session content
        if best_match_end == len(query) - 1:
            break

    return bbxs


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


def main():
    # delete everything in the results folder
    # shutil.rmtree('./results', ignore_errors=True)

    script_reader: ScriptReader = ScriptReader(
        './testing_xml',
        './testing_pdf',
    )

    SUCCESSFUL: int = 0
    UNSUCCESSFUL: int = 0

    for idx, (xml_file_path, pdf_file_path) in enumerate(script_reader.group_xml_pdf()):
        xml_editor: XMLEditor = XMLEditor(xml_file_path)

        # get a list of note elements from xml
        notes_ET: list[ET.Element] = xml_editor.get_elements_by_tags(NOTE_TAG)
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

        notes_str_1: list[str] = [get_text_from_element(note) for note in notes_ET_time]

        # get GER note that indicates beginning of the session content
        # we always select the GER one because after the GER note there is always session content
        session_start_note: str = notes_str_1[0] if notes_str_1 else notes_str[0]

        # get a list of sentence elements from xml and convert them to list of strings
        # and remove firs note elements that indicate time
        sentences_ET1: list[ET.Element] = xml_editor.get_elements_by_tags(SENTENCE_TAG)
        i_from = sentences_ET1.index(notes_ET_time[0])
        sentences_ET1 = sentences_ET1[i_from + 1:]
        sentences_ET2: list[ET.Element] = xml_editor.get_elements_by_tags(SENTENCE_TAG)[2:]
        sentences_ET2 = sentences_ET2[i_from + 1:]

        # get a list of all words in the pdf
        pdf_words1, pdf_words_excluded1 = get_words_from_pdf(pdf_file_path, session_start_note, session_end_note)
        pdf_words2, pdf_words_excluded2 = get_words_from_pdf(pdf_file_path, session_start_note, session_end_note)

        excluded_titles_full, excluded_titles_slo, excluded_titles_ger = make_regex_for_excluded_words1(
            pdf_words_excluded2)

        try:
            bbxs = search_for_words_all(pdf_words1, sentences_ET1)

            print(f'{idx}. WORKS ON: {pdf_file_path}')
            SUCCESSFUL += 1

        except Exception as e:

            print(f'{idx} TRYING HARDER ON: {pdf_file_path}')

            try:
                s1 = sentences_ET2[:]
                s2 = sentences_ET2[:]
                s3 = sentences_ET2[:]
                s4 = sentences_ET2[:]

                pdf_words2 = remove_titles(pdf_words2, s1, excluded_titles_full)
                pdf_words2 = remove_titles(pdf_words2, s2, excluded_titles_slo)
                pdf_words2 = remove_titles(pdf_words2, s3, excluded_titles_ger)

                bbxs = search_for_words_limited(pdf_words2, s4)
                print(f'{idx}. WORKS ON: {pdf_file_path}')
                SUCCESSFUL += 1

            except Exception as e:

                print(f'{idx}. DOES NOT WORK ON: {pdf_file_path}')
                traceback.print_exc()
                UNSUCCESSFUL += 1

                # copy the pdf file to the exceptions_test folder
                shutil.copy(pdf_file_path, f'exceptions/pdf/{os.path.basename(pdf_file_path)}')
                shutil.copy(xml_file_path, f'exceptions/xml/{os.path.basename(xml_file_path)}')
                continue

        # display the result
        # xml_editor.save(f'./output')
        # get the base name of the xml file
        # file_name = os.path.basename(xml_file_path)
        # prepare_result1(f'./output/{file_name}', pdf_file_path)
        prepare_result(xml_file_path, pdf_file_path, bbxs)

    # print the results
    print(f'SUCCESSFUL: {SUCCESSFUL}')
    print(f'UNSUCCESSFUL: {UNSUCCESSFUL}')
    # print(f'%: {SUCCESSFUL / (SUCCESSFUL + UNSUCCESSFUL) * 100}')


if __name__ == '__main__':
    main()
