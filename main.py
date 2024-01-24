import os

from api.metin2wiki import Metin2Wiki
from api.mediawiki import Bot, BotManagement
from models.page import MonsterPage, MetinPage, Page, create_monster_page
from data.read_files import MobProto, ItemProto, MobDrop, ItemName
from UI.graphic import WikiApp

# def create_wiki_monster_data():
#     metin2wiki = Metin2Wiki(bot_name=BOT_NAME, bot_password=BOT_PASSWORD)

#     metin2wiki.login()

#     monster_pages = metin2wiki.category("Monstres (temporaire)")
#     monster_pages = metin2wiki.pages(monster_pages)
#     monster_pages = [MonsterPage(page) for page in monster_pages.content(parse=True)]

#     metin_pages = metin2wiki.category("Pierres Metin")
#     metin_pages = metin2wiki.pages(metin_pages)
#     metin_pages = [MetinPage(page) for page in metin_pages.content(parse=True)]

#     monster_pages += metin_pages

#     monster_pages.sort(key=lambda x: x.vnum)

#     mob_proto = MobProto(processing="wiki_data")

#     vnums, titles = zip(*[[page.vnum, page.title] for page in monster_pages])

#     mob_proto.create_wiki_monster_data(vnums=vnums, titles=titles)


if __name__ == "__main__":
    # wiki_app = WikiApp()
    # wiki_app.mainloop()
    # mob_proto = MobProto(processing="default").data
    # item_names = ItemName().data["LOCALE_NAME"]
    # mob_drop = MobDrop(item_names).data
    # create_monster_page(5163, mob_proto, mob_drop, localisation="I", zone="[[Repaire de Meley]]")

    bot = Bot(name="AbeilleBot@AbeilleBot", password="ligkhmees4pvg4e9563a4452dcihkasp")
    metin2wiki = Metin2Wiki(bot=bot)
    metin2wiki.login()
    pages = metin2wiki.category("Monstres (temporaire)")
    pages = metin2wiki.get_content(pages)
    pages = metin2wiki.pages(pages, category="monster")

    pages = sorted(pages, key=lambda page: page.vnum)

    with open('res.txt', "w") as file:

        for page in pages:
            name: str = page.title
            content: str = page.template

            name_info = name.split(' (')
            image = content.get("Image").value.strip()
            DC = False

            if ('|Compétence=' in content) or ('|NombreCompétence=' in content):
                DC = True

            element = content.get('élément'.capitalize()).value.strip()

            element_index = 4
            skill_index = 6

            template = [
                "{{Monstres/Résumé",
                f"|Nom={name}",
                f"|Niveaux={content.get('Niveau').value.strip()}, {content.get('Rang').value.strip()}",
                f"|Élément={element}",
                f"|Type={content.get('Type').value.strip()}",
                f"|Dégât={content.get('Dégâts').value.strip()}",
                f"|Image={image}-min",
                "}}"
            ]

            if len(name_info) == 2:
                template.insert(2, f"|NomRéel={name_info[0]}")
                element_index += 1
                skill_index += 1

            if content.has("élément2".capitalize()):
                template.insert(element_index, f"|Élément2={content.get("élément2".capitalize()).value.strip()}")
                skill_index += 1

            if DC:
                template.insert(skill_index, f"|DC=True")

            template = "\n".join(template)
                
            print(template, file = file)