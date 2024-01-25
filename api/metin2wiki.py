import polars as pl

from api.mediawiki import MediaWiki, Bot


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

    def get_monsters_and_stones(self):
        pages = self.category("Monstres (temporaire)") + self.category("Pierres Metin")
        pages = self.get_content(pages)
        pages = self.pages(pages)
        return ((page.vnum, page.title) for page in pages)
