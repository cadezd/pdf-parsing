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
        self.tree.write(os.path.join(folder, self.name))
