from typing import Literal
import mwparserfromhell
from mwparserfromhell.wikicode import Wikicode
from mwparserfromhell.nodes.template import Template
from mwparserfromhell.nodes.extras.parameter import Parameter
from mwparserfromhell.nodes.wikilink import Wikilink

from utils.utils import code_to_vnum, vnum_conversion, image_formatting
from data.read_files import MobProto, MobDropItem


class Page:
    def __init__(
        self,
        data: dict,
    ):
        self.title: str = data["title"]
        self.pageid: int = data["pageid"]
        self.content = self.get_content(data)
        self._vnum = None
        self._templates = None

    @property
    def vnum(self):
        if self._vnum is not None:
            return self._vnum
        templates = self.templates
        if templates is not None:
            return self._get_vnum(templates[0])
    
    @property
    def templates(self) -> None | list[Template]:
        if self._templates is not None:
            return self._templates
        if self.content is None:
            return None
        return self.content.filter(Template)
    
    def _get_vnum(self, template: Template):
        code: Parameter = template.get("Code")
        return code_to_vnum(code.value.strip_code())
    
    def get_content(self, data: dict):
        if "revisions" in data:
            return mwparserfromhell.parse(data["revisions"][0]["content"])
        return None

    def __str__(self):
        return f"(Page: [title: {self.title}])"

    def get_parameter_value(self, parameter_name: str):
        parameter: Parameter = self.templates[0].get(parameter_name)
        return parameter.value.strip_code()
    
    def has_parameter(self, parameter_name: str):
        return self.templates[0].has(parameter_name)

    def to_card(self):
        template_name = "Monstres/Résumé\n"
        splitted_name = self.title.split(" (")

        template = Template(template_name)
        template.add(name="Nom", value=self.title + "\n")

        if len(splitted_name) == 2:
            template.add(name="NomRéel", value=splitted_name[0])

        template.add(name="Niveaux", value=f"{self.get_parameter_value("Niveau")}, {self.get_parameter_value("Rang")}")
        template.add(name="Élément", value=self.get_parameter_value("Élément"))

        if self.has_parameter("Élément2"):
            template.add(name="Élément2", value=self.get_parameter_value("Élément2"))

        template.add(name="Type", value=self.get_parameter_value("Type"))
        template.add(name="Dégât", value=self.get_parameter_value("Dégâts"))

        if self.has_parameter("Compétence") or self.has_parameter("NombreCompétence"):
            template.add(name="DC", value="True")

        template.add(name="Image", value=f"{self.get_parameter_value("Image")}-min")

        return template
    
    @staticmethod
    def _new_monster_page(vnum: int, localisation="", zone="", lang="fr"):
        mob_data = MobProto().get_data_for_pages(vnum, lang, to_dicts=True)[0]
        mob_drop_item = MobDropItem()
        elements = mob_data["Élément"]

        template = Template(name="Monstres\n")
        template.add(name="Code", value=vnum_conversion(vnum) + "\n")
        template.add(name="Image", value=image_formatting(mob_data["LOCALE_NAME"]))
        parameters = ["Niveau", "Rang", "Type", "Exp", "Dégâts", "Agressif", "Poison", "Ralentissement", "Étourdissement"]
        
        for param in parameters:
            template.add(name=param, value=mob_data[param])

        template.add(name="Élément", value=elements[0], before="Dégâts")

        if len(elements) == 2:
            template.add(name="Élément2", value=elements[1], before="Dégâts")

        template.add(name="Repousser", value="")
        template.add(name="Localisation", value=localisation)
        template.add(name="Zones", value=zone)
        template.add(name="Lâche", value="")

        if mob_data["PM"]:
            template.add(name="PM", value=mob_data["PM"])

        template.add(name="InfoSup", value="")

        if vnum in mob_drop_item:
            print(mob_drop_item[vnum])

        print(mob_data["Drop"])
        print(template)

        if vnum in mob_drop_item:
            param = template.get("Lâche")

            for item_list in mob_drop_item[vnum]:
                drop_template = Template("Drop\n")
                drop_template.add(name="Catégorie", value="\n")

                for index, item in enumerate(item_list):
                    L_template = Template("L")
                    item_image = image_formatting(item)
                    L_template.add(name="1", value=item_image)
                    if item_image != item:
                        L_template.add(name="2", value=item)

                    drop_template.add(name=index+1, value=str(L_template) + "\n", preserve_spacing=False)
                    param.value = "\n" + str(drop_template) + "\n"

    @staticmethod
    def new_page(category: Literal["mob"], vnum: int, localisation="", zone=""):
        if category == "mob":
            Page._new_monster_page(vnum, localisation, zone)
