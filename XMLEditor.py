import os
import xml.etree.ElementTree as ET


class XMLEditor:
    def __init__(self, xml_path: str):
        ET.register_namespace('', 'http://www.tei-c.org/ns/1.0')
        self.xml_path: str = xml_path
        self.name = os.path.basename(xml_path)
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()

    def get_elements_by_tags(self, tags: list[str], ignore_tags: list[str] = None) -> list[ET.Element]:
        """
        Returns list of elements with given tags
        :param tags: list[str]
        :param ignore_tags: list[str]
        :return: list[ET.Element]
        """
        return self._get_elements_by_tags(self.root, tags, [], ignore_tags)

    def _get_elements_by_tags(self, element: ET.Element, tags: list[str], result: list[ET.Element],
                              ignore_tags: list[str] = None) -> list[ET.Element]:
        """
        Recursive function to get elements by tags.
        :param element: ET.Element
        :param tags: list[str]
        :param result: list[ET.Element]
        :param ignore_tags: list[str]
        """

        for child in element:
            # ignores given tags and their children
            if ignore_tags and child.tag in ignore_tags:
                continue

            # collects elements with given tags
            if child.tag in tags:
                result.append(child)

            self._get_elements_by_tags(child, tags, result, ignore_tags)

        return result

    def save(self, folder: str):
        """Save the xml file to the folder."""
        self.tree.write(os.path.join(folder, self.name), encoding='utf-8')

    def add_coordinates_to_sentences(self):
        """
        Adds coordinates to sentences
        """
        sentences = self.get_elements_by_tags(['{http://www.tei-c.org/ns/1.0}s'])
        for sentence in sentences:
            # get first and last word in sentence
            words = sentence.findall('.//{http://www.tei-c.org/ns/1.0}w')
            if not words:
                continue

            firstWord = words[0]
            lastWord = words[-1]

            # get attributes of from first and last word to put in sentence
            fromPage = firstWord.get('fromPage')
            toPage = lastWord.get('toPage')
            x1 = firstWord.get('x1')
            y1 = firstWord.get('y1')
            x2 = lastWord.get('x2') if lastWord.get('isOnMultipleLines') == 'False' else lastWord.get('x4')
            y2 = lastWord.get('y2') if lastWord.get('isOnMultipleLines') == 'False' else lastWord.get('y4')

            # add attributes to sentence
            sentence.set('fromPage', fromPage)
            sentence.set('toPage', toPage)
            sentence.set('x1', x1)
            sentence.set('y1', y1)
            sentence.set('x2', x2)
            sentence.set('y2', y2)

    def add_coordinates_to_segments(self):
        """
        Adds coordinates to segments
        """
        segments = self.get_elements_by_tags(['{http://www.tei-c.org/ns/1.0}seg'])
        for segment in segments:
            # get first and last sentence in segment
            sentences = segment.findall('.//{http://www.tei-c.org/ns/1.0}s')
            if not sentences:
                continue

            firstSentence = sentences[0]
            lastSentence = sentences[-1]

            # get attributes of from first and last sentence to put in segment
            fromPage = firstSentence.get('fromPage')
            toPage = lastSentence.get('toPage')
            x1 = firstSentence.get('x1')
            y1 = firstSentence.get('y1')
            x2 = lastSentence.get('x2')
            y2 = lastSentence.get('y2')

            # add attributes to segment
            segment.set('fromPage', fromPage)
            segment.set('toPage', toPage)
            segment.set('x1', x1)
            segment.set('y1', y1)
            segment.set('x2', x2)
            segment.set('y2', y2)