from mwparserfromhell.wikicode import Wikicode
from mwparserfromhell.nodes.template import Template
from mwparserfromhell.nodes.extras.parameter import Parameter
from mwparserfromhell.nodes.wikilink import Wikilink

from utils.utils import image_formatting


class L(Template):
    def __init__(self, item_name: str):
        super().__init__(name="L")
        image_name = image_formatting(item_name)
        if item_name == image_name:
            self.add("1", item_name)
        else:
            self.add("1", image_name)
            self.add("2", item_name)

        self._item_name = item_name
        self._image_name = image_name

    def item_name(self):
        return self._item_name
    
    def image_name(self):
        return self._image_name