import os

from api.metin2wiki import Metin2Wiki
from models.page import MonsterPage, MetinPage, Page, Pages
from data.read_files import MobProto, ItemProto
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
    wiki_app = WikiApp()
    wiki_app.mainloop()