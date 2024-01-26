import os

import polars as pl

from api.metin2wiki import Metin2Wiki
from api.mediawiki import Bot, BotManagement
from models.page import MonsterPage, MetinPage, Page, create_monster_page
from data.read_files import GameProto, GameNames
from UI.graphic import WikiApp


if __name__ == "__main__":
    # wiki_app = WikiApp()
    # wiki_app.mainloop()
    # mob_proto = MobProto(processing="default").data
    # item_names = ItemName().data["LOCALE_NAME"]
    # mob_drop = MobDrop(item_names).data
    # create_monster_page(5163, mob_proto, mob_drop, localisation="I", zone="[[Repaire de Meley]]")

    metin2wiki = Metin2Wiki(bot=bot)
    metin2wiki.login()
    metin2wiki.save_data_for_calculator()

    # pages = metin2wiki.category("Monstres (temporaire)")
    # pages = metin2wiki.get_content(pages)
    # pages = metin2wiki.pages(pages, category="monster")

    # pages = sorted(pages, key=lambda page: page.vnum)

    # with open('res.txt', "w") as file:

    #     for page in pages:
    #         name: str = page.title
    #         content: str = page.template

    #         name_info = name.split(' (')
    #         image = content.get("Image").value.strip()
    #         DC = False

    #         if ('|Compétence=' in content) or ('|NombreCompétence=' in content):
    #             DC = True

    #         element = content.get('élément'.capitalize()).value.strip()

    #         element_index = 4
    #         skill_index = 6

    #         template = [
    #             "{{Monstres/Résumé",
    #             f"|Nom={name}",
    #             f"|Niveaux={content.get('Niveau').value.strip()}, {content.get('Rang').value.strip()}",
    #             f"|Élément={element}",
    #             f"|Type={content.get('Type').value.strip()}",
    #             f"|Dégât={content.get('Dégâts').value.strip()}",
    #             f"|Image={image}-min",
    #             "}}"
    #         ]

    #         if len(name_info) == 2:
    #             template.insert(2, f"|NomRéel={name_info[0]}")
    #             element_index += 1
    #             skill_index += 1

    #         if content.has("élément2".capitalize()):
    #             template.insert(element_index, f"|Élément2={content.get("élément2".capitalize()).value.strip()}")
    #             skill_index += 1

    #         if DC:
    #             template.insert(skill_index, f"|DC=True")

    #         template = "\n".join(template)
                
    #         print(template, file = file)