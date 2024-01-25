import polars as pl

from api.mediawiki import MediaWiki, Bot
from data.read_files import GameProto


class Metin2Wiki(MediaWiki):
    ALPHABET = "abcdefghijklmnopqrstuvwxyz"
    ALPHABET += ALPHABET.upper()
    BASE = len(ALPHABET)

    BASE_URL = "https://{lang}-wiki.metin2.gameforge.com/api.php"

    def __init__(
        self,
        lang="fr",
        bot: Bot = None,
    ):
        super().__init__(
            api_url=self.construct_api_url(lang=lang),
            bot=bot,
        )
        self.lang = lang

    def construct_api_url(self, lang: str):
        return self.BASE_URL.format(lang=lang)

    def change_lang(self, new_lang: str):
        self.api_url = self.construct_api_url(lang=new_lang)
        self.lang = new_lang

    def save_data_for_calculator(self):
        game_proto = GameProto()
        pages = self.category("Monstres (temporaire)") + self.category("Pierres Metin")
        pages = self.get_content(pages)
        game_proto.save_mob_data_for_calculator(
            (page.vnum, page.title) for page in self.pages(pages)
        )

    def test(self):
        game_proto = GameProto()
        pages = self.category("Armes")
        pages = self.get_content(pages)
        game_proto.test([page.vnum for page in self.pages(pages)])
