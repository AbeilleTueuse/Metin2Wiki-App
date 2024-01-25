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

    def vnum_conversion(self, number: int):
        if number == 0:
            return "a"

        converted_number = ""

        while number > 0:
            number, remainder = divmod(number, self.BASE)
            converted_number += self.ALPHABET[remainder]

        return converted_number

    def code_to_vnum(self, letters: str) -> int:
        number = 0

        for i, letter in enumerate(letters):
            value = self.ALPHABET.index(letter)
            number += value * (self.BASE**i)

        return number
    
    def get_monster_and_stone_vnums(self):
        pages = self.category("Monstres (temporaire)") + self.category("Pierres Metin")
        pages = self.get_content(pages)
        pages = self.pages(pages)
        return [page.vnum for page in pages]
