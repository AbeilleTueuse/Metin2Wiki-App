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

    metin2wiki = Metin2Wiki(bot=True)
    metin2wiki.login()
    metin2wiki.save_data_for_monster_page()