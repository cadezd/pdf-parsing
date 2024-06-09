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
SENTENCE_TAG: list[str] = ['s']
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


def prepare_result(xml_path: str, pdf_path: str, bbxs: list[tuple[int, float, float, float, float]], _from: int = -1,
                   _to: int = -1):
    # create folder from the xml file name in the results folder
    file_name = os.path.basename(xml_path).split('.')[0]
    folder = os.path.join('./results', file_name)
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


def get_words_from_pdf(pdf_path: str, start_of_session: str, end_of_session: str, remove_titles: bool = False) -> tuple[
    list[dict], list[str]]:
    # list that will store all words in the pdf
    all_pdf_words: list[dict] = []
    pdf_words_excluded: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        # iterating through pages and getting all words on each page
        for page_no, pdf_page in enumerate(pdf.pages):
            # get all words based on PDF's underlying flow of characters
            page_words: list[dict] = pdf_page.extract_words(use_text_flow=True, x_tolerance=5)

            # skipping pages with no words
            if not page_words:
                continue

            # adding page no to each word
            page_words = [{'page_no': page_no, **word} for word in page_words]

            if remove_titles:
                page_words_wanted = []
                page_words_excluded = []

                # ignore title at the top of the page
                words = [w['text'].strip() for w in page_words]
                text = ' '.join([w['text'].strip() for w in page_words])
                first_word = page_words[0]
                second_word = page_words[1] if len(page_words) > 1 else None

                for n in roman_numeros:
                    if n in first_word['text'] or (n in second_word['text']):
                        rest_of_text = text.strip()[text.strip().find(n) + len(n):].lower().replace(' ', '')
                        if len(words) > 4 and n in words[4:]:
                            # keep only words that have top coordinate lower that bottom coordinate of first word
                            page_words_excluded = ' '.join(
                                [w['text'] for w in page_words if w['top'] <= first_word['bottom']])
                            page_words_wanted = [w for w in page_words if w['top'] > first_word['bottom']]

                        if "stihma" in rest_of_text or "sitzungun" in rest_of_text or "sejadne" in rest_of_text or "sitzungam" in rest_of_text or "sitzungmn" in rest_of_text or "sitzungant" in rest_of_text or "sitzungnm" in rest_of_text:
                            # keep only words that have top coordinate lower that bottom coordinate of first word
                            page_words_excluded = ' '.join(
                                [w['text'] for w in page_words if w['top'] <= first_word['bottom']])
                            page_words_wanted = [w for w in page_words if w['top'] > first_word['bottom']]

                        part2 = text.strip().split(chr(8212))  # U+8212 je Em Dash (pomišljaj)
                        if len(part2) > 1 and part2[1].strip().startswith(n):
                            # keep only words that have top coordinate lower that bottom coordinate of first word
                            page_words_excluded = ' '.join(
                                [w['text'] for w in page_words if w['top'] <= first_word['bottom']])
                            page_words_wanted = [w for w in page_words if w['top'] > first_word['bottom']]

                all_pdf_words.extend(page_words_wanted)
                pdf_words_excluded.append(page_words_excluded)

            else:
                all_pdf_words.extend(page_words)
                pdf_words_excluded = []

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



def handle_exception(pdf_words: list[dict], sentences_str: list[str], words_ET: list[ET.Element],
                     excluded_words: list[str]) -> list[tuple[int, float, float, float, float]]:
    bbxs: list[tuple[int, float, float, float, float]] = []

    # all words from pdf concatenated
    query: str = ' '.join([w['text'] for w in pdf_words])

    best_match_start: int = 0
    best_match_end: int = 0

    result = {'locations': []}
    search_area_start: int = 0

    while sentences_str:
        zero_length_target: bool = False

        # sentence from xml that we want to find in the pdf
        target: str = remove_excluded_words(sentences_str.pop(0), excluded_words)

        similarity: float = 0
        BUFFER: int = 10

        no_of_words = len(target.split(' '))
        if no_of_words == 1:
            SIMILARITY_THRESHOLD = 0.000000001
        elif 1 < no_of_words < 3:
            SIMILARITY_THRESHOLD = 0.3
        elif 3 <= no_of_words < 5:
            SIMILARITY_THRESHOLD = 0.5
        elif 5 <= no_of_words < 10:
            SIMILARITY_THRESHOLD = 0.6
        elif 10 <= no_of_words < 20:
            SIMILARITY_THRESHOLD = 0.75
        else:
            SIMILARITY_THRESHOLD = 0.75

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

            if len(target) == 0:
                zero_length_target = True
                break

            similarity = 1 - result['editDistance'] / len(target)
            BUFFER += 10

            print(similarity)
            print(search_area_start, search_area_end)
            print(query_limited)
            print(target)
            print()

            # time.sleep(5)

            if BUFFER > BUFFER_LIMIT:
                print()
                print(sentences_str.pop(0))
                raise Exception('BUFFER is too big')

        print(target)
        print(similarity)
        print()

        if zero_length_target:
            continue

        best_match_start: int = search_area_start + result['locations'][0][0]
        best_match_end: int = search_area_start + result['locations'][0][-1]

        idx = 0
        for word in pdf_words:
            if best_match_start <= idx <= best_match_end:
                if (word['page_no'], word['x0'], word['top'], word['x1'], word['bottom']) not in bbxs:
                    bbxs.append((word['page_no'], word['x0'], word['top'], word['x1'], word['bottom']))
            if idx > best_match_end:
                break
            idx += len(word['text']) + 1

        # stop when reaching the end of the session content
        if best_match_end == len(query) - 1 and is_last_sentence(target):
            break

    return bbxs


def get_coordinates(pdf_words: list[dict], sentences_str: list[str], words_ET: list[ET.Element],
                    excluded_words: list[str]) -> list[tuple[int, float, float, float, float]]:
    bbxs: list[tuple[int, float, float, float, float]] = []

    # all words from pdf concatenated
    query: str = ' '.join([w['text'] for w in pdf_words])

    search_from: int = 0

    while sentences_str:

        # sentence from xml that we want to find in the pdf
        target: str = sentences_str.pop(0)

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
        best_match_start = search_from + result['locations'][0][0] if result['locations'][0][0] else 1
        best_match_end = search_from + result['locations'][0][-1]

        print(query_limited)
        print(target)
        print(similarity)
        print(search_from)
        print()

        if similarity < 0.3:
            print(similarity)
            raise Exception('Similarity is too low')

        search_from = best_match_end + 1

        # getting data for the bounding box for the target sentence
        idx = 0
        for word in pdf_words:
            if best_match_start <= idx <= best_match_end:
                if (word['page_no'], word['x0'], word['top'], word['x1'], word['bottom']) not in bbxs:
                    bbxs.append((word['page_no'], word['x0'], word['top'], word['x1'], word['bottom']))
            if idx > best_match_end:
                break
            idx += len(word['text']) + 1

        # stop when reaching the end of the session content
        if best_match_end == len(query) - 1 or is_last_sentence(target):
            break

    return bbxs


def main():
    # delete everything in the results folder
    # shutil.rmtree('./results', ignore_errors=True)

    script_reader: ScriptReader = ScriptReader(
        './all_xml',
        './all_pdf',
        _idx=15,
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

        # keep only notes that have type time and are in German
        notes_ET_1 = list(
            filter(lambda n: 'type' in n.attrib and n.attrib['type'] == 'time' and \
                             '{http://www.w3.org/XML/1998/namespace}lang' in n.attrib and \
                             n.attrib['{http://www.w3.org/XML/1998/namespace}lang'] == 'de',
                   notes_ET)
        )

        notes_str_1: list[str] = [get_text_from_element(note) for note in notes_ET_1]

        # get GER note that indicates beginning of the session content
        # we always select the GER one because after the GER note there is always session content
        session_start_note: str = notes_str_1[0] if notes_str_1 else notes_str[0]

        #print(session_start_note, '|', session_end_note)

        # get a list of sentence elements from xml and convert them to list of strings
        sentences_ET: list[ET.Element] = xml_editor.get_elements_by_tags(SENTENCE_TAG)
        sentences_str1: list[str] = [get_text_from_element(sentence) for sentence in sentences_ET]
        sentences_str2: list[str] = [get_text_from_element(sentence) for sentence in sentences_ET]

        # get word elements from xml and convert them to list of strings
        words_ET: list[ET.Element] = xml_editor.get_elements_by_tags(WORD_TAG)

        # get a list of all words in the pdf
        pdf_words1, pdf_words_excluded1 = get_words_from_pdf(pdf_file_path, session_start_note, session_end_note)
        pdf_words2, pdf_words_excluded2 = get_words_from_pdf(pdf_file_path, session_start_note, session_end_note)


        try:
            bbxs: list[tuple[int, float, float, float, float]] = get_coordinates(pdf_words1, sentences_str1, words_ET,
                                                                                 pdf_words_excluded1)
            print(f'{idx}. WORKS ON: {pdf_file_path}')
            SUCCESSFUL += 1
        except Exception as e:
            print(f'{idx} TRYING HARDER ON: {pdf_file_path}')
            traceback.print_exc()
            try:
                bbxs: list[tuple[int, float, float, float, float]] = handle_exception(pdf_words2, sentences_str2,
                                                                                      words_ET, pdf_words_excluded2)
                print(f'{idx}. WORKS ON: {pdf_file_path}')
                SUCCESSFUL += 1
            except Exception as e:
                print(f'{idx}. DOES NOT WORK ON: {pdf_file_path}')
                traceback.print_exc()
                UNSUCCESSFUL += 1

                # copy the pdf file to the exceptions folder
                shutil.copy(pdf_file_path, f'./exceptions/pdf/{os.path.basename(pdf_file_path)}')
                shutil.copy(xml_file_path, f'./exceptions/xml/{os.path.basename(xml_file_path)}')
                continue

        # display the result
        prepare_result(xml_file_path, pdf_file_path, bbxs)
        xml_editor.save(f'./output')

    # print the results
    print(f'SUCCESSFUL: {SUCCESSFUL}')
    print(f'UNSUCCESSFUL: {UNSUCCESSFUL}')
    print(f'%: {SUCCESSFUL / (SUCCESSFUL + UNSUCCESSFUL) * 100}')


if __name__ == '__main__':
    main()
