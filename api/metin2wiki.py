import polars as pl

from api.mediawiki import MediaWiki, Bot
from data.read_files import (
    MobProto,
    ItemProto,
    ItemNames,
    CALCULATOR_DATA_PATH,
    MONSTER_DATA_PATH,
)


class Metin2Wiki(MediaWiki):
    ALPHABET = "abcdefghijklmnopqrstuvwxyz"
    ALPHABET += ALPHABET.upper()
    BASE = len(ALPHABET)

    BASE_URL = "https://{lang}-wiki.metin2.gameforge.com/api.php"

    def __init__(
        self,
        lang="fr",
        bot: Bot | bool = None,
    ):
        super().__init__(
            api_url=self.construct_api_url(lang=lang),
            lang=lang,
            bot=bot,
        )

    def construct_api_url(self, lang: str):
        return self.BASE_URL.format(lang=lang)

    def change_lang(self, new_lang: str):
        self.api_url = self.construct_api_url(lang=new_lang)
        self.lang = new_lang

    def _get_mob_data_for_calculator(self):
        pages = self.category("Monstres (temporaire)") + self.category("Pierres Metin")
        pages = self.get_content(pages)
        mob_proto = MobProto()

        return mob_proto.get_mob_data_for_calculator(
            (page.vnum, page.title) for page in self.pages(pages)
        )

    def _get_item_data_for_calculator(self):
        item_proto = ItemProto()
        item_names = ItemNames(lang=self.lang)
        en_names = ItemNames(lang="en")
        pages = self.category("Armes")
        pages = self.get_content(pages)

        return item_proto.get_item_data_for_calculator(
            [page.vnum for page in self.pages(pages)], item_names, en_names
        )

    def save_data_for_calculator(self):
        item_data = self._get_item_data_for_calculator()
        mob_data = self._get_mob_data_for_calculator()

        with open(CALCULATOR_DATA_PATH, "w") as file:
            print(
                f"var weaponData = {item_data}",
                f"var monsterData = {mob_data}",
                sep="\n\n",
                file=file,
            )
            print(f"Data saved as {CALCULATOR_DATA_PATH}.")

    def save_data_for_monster_page(self):
        pages = self.category("Monstres (temporaire)")
        pages = self.get_content(pages)
        pages = self.pages(pages, sort_by_vnum=True)

        with open(MONSTER_DATA_PATH, "w") as file:
            for page in pages:
                print(page.to_card(), file=file)
            print(f"Data saved as {MONSTER_DATA_PATH}.")
