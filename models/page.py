from typing import Literal
import mwparserfromhell
from mwparserfromhell.wikicode import Wikicode
from mwparserfromhell.nodes.template import Template
from mwparserfromhell.nodes.extras.parameter import Parameter
from mwparserfromhell.nodes.wikilink import Wikilink
from unidecode import unidecode

from utils.utils import code_to_vnum


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

    def split_name(self):
        sep = r" ("
        return self.title.split(sep)

    def to_card(self):
        template_name = "Monstres/Résumé\n"
        splitted_name = self.split_name()

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


    
class EntityPage(Page):
    def __init__(self, data: dict, entity: Literal["Monstres", "Metin"] = "Monstre"):
        super().__init__(data=data)
        self.entity = entity
        self.template = self.content.filter(Template)[0]
        self.vnum = self._get_vnum()

    def _get_vnum(self):
        return code_to_vnum(self.template.get("Code").value.strip())

    def get_parameters(self):
        return super().get_parameters(self.template)

    # def get_proto_values(self):

    #     values = {parameter: str(self.template.get(parameter).value).strip() for parameter in self.PROTO_PARAMETERS['obligatory']}
    #     values['Agressif'] = values['Agressif'].replace('NO', 'N')
    #     if self.template.has('Nom'):
    #         values['Nom'] = str(self.template.get('Nom').value).strip()
    #     else:
    #         if not self.name.endswith('(quête)'):
    #             values['Nom'] = self.name.split(' (')[0]
    #         else:
    #             values['Nom'] = self.name

    #     if self.template.has('Élément2'):
    #         values['Élément'] += f'|{str(self.template.get("Élément2").value).strip()}'

    #     if self.template.has('PM'):
    #         values['PM'] = str(self.template.get('PM').value).strip()

    #    return values

    # def compare_with_proto(self, proto):

    #     proto_values = self.get_proto_values()
    #     proto_true = proto.loc[self.vnum]

    #     for parameter_name in proto_values:
    #         if proto_values[parameter_name] != proto_true[parameter_name]:
    #             print(f'Monster: {self.name} ({self.vnum}), error: {parameter_name} ({proto_values[parameter_name]} instead of {proto_true[parameter_name]})')

    #     if (proto_true['PM']) != '0' or ('PM' in proto_values):
    #         if proto_true['PM'] != proto_values['PM']:
    #             print(f'Monster: {self.name} ({self.vnum}), error: PM ({proto_values["PM"]} instead of {proto_true["PM"]})')

    def add_parameter(
        self, parameter_name: str, parameter_value: str, before: str | None = None
    ):
        return super().add_parameter(
            self.template, parameter_name, parameter_value, before
        )

    def change_parameter_name(self, parameter_name: str, new_parameter_name: str):
        return super().change_parameter_name(
            self.template, parameter_name, new_parameter_name
        )

    def change_parameter_value(self, parameter_name: str, new_parameter_value: str):
        return super().change_parameter_value(
            self.template, parameter_name, new_parameter_value
        )

    def delete_parameter(self, parameter_name: str):
        return super().delete_parameter(self.template, parameter_name)


class MonsterPage(EntityPage):
    def __init__(self, data: dict):
        super().__init__(data=data, entity="Monstres")


class MetinPage(EntityPage):
    def __init__(self, page: Page):
        super().__init__(page=page, entity="Metin")

def vnum_conversion(number: int):
    ALPHABET = "abcdefghijklmnopqrstuvwxyz"
    ALPHABET += ALPHABET.upper()
    BASE = len(ALPHABET)

    if number == 0:
        return "a"

    converted_number = ""

    while number > 0:
        number, remainder = divmod(number, BASE)
        converted_number += ALPHABET[remainder]

    return converted_number

def image_formatting(name: str):
    if isinstance(name, int):
        return name
    if name[-2] == "+" and name[-1].isdigit():
        name = name[:-2]
    return "".join(letter for letter in unidecode(name.lower()) if letter.isalnum()).capitalize()

def create_monster_page(vnum, mob_proto, mob_drop, localisation="", zone=""):
    mob_data = mob_proto.loc[vnum]
    template = Template(name="Monstres\n")
    template.add(name="Code", value=vnum_conversion(vnum) + "\n")
    template.add(name="Image", value=image_formatting(mob_data["NameFR"]))
    parameters = ["Niveau", "Rang", "Type", "Exp", "Élément", "Dégâts", "Agressif", "Poison", "Ralentissement", "Étourdissement"]
    
    for param in parameters:
        template.add(name=param, value=mob_data[param])

    template.add(name="Repousser", value="")
    template.add(name="Localisation", value=localisation)
    template.add(name="Zones", value=zone)
    template.add(name="Lâche", value="")
    if int(mob_data["PM"]):
        template.add(name="PM", value=mob_data["PM"])
    template.add(name="InfoSup", value="")

    if vnum in mob_drop:
        param = template.get("Lâche")
        drop_template = Template("Drop\n")
        drop_template.add(name="Catégorie", value="\n")
        for index, item in enumerate(mob_drop[vnum]):
            L_template = Template("L")
            item_image = image_formatting(item)
            L_template.add(name="1", value=item_image)
            if item_image != item:
                L_template.add(name="2", value=item)

            drop_template.add(name=index+1, value=str(L_template) + "\n", preserve_spacing=False)
            param.value = "\n" + str(drop_template) + "\n"

    print(template)
    

