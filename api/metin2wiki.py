from api.mediawiki import MediaWiki, Bot, BotManagement


class Metin2Wiki(MediaWiki):
    ALPHABET = "abcdefghijklmnopqrstuvwxyz"
    ALPHABET += ALPHABET.upper()
    BASE = len(ALPHABET)

    BASE_URL = "https://{lang}-wiki.metin2.gameforge.com/api.php"

    ALL_LANG = [
        "ae",
        "cz",
        "de",
        "en",
        "es",
        "fr",
        "gr",
        "hu",
        "it",
        "nl",
        "pl",
        "pt",
        "ro",
        "tr",
    ]

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
        self.bot_management = BotManagement(lang=lang)

    def construct_api_url(self, lang: str):
        return self.BASE_URL.format(lang=lang)

    def change_lang(self, new_lang: str):
        self.api_url = self.construct_api_url(lang=new_lang)
        self.lang = new_lang
        self.bot_management.change_lang(new_lang=new_lang)

    def set_default_bot(self):
        bot = self.bot_management.get_default_bot()
        self.set_bot(bot)
        if bot is None:
            return None
        return bot.name

    def change_default_bot(self, bot_name: str):
        bot = self.bot_management.change_default_bot(bot_name)
        self.set_bot(bot)

    def set_bot(self, bot: Bot | None = None):
        self.bot = bot
        self.csrf_token = None
        self.logout()

    def delete_bot(self):
        self.set_bot(bot=None)

    def get_number_of_bots(self):
        return len(self.bot_management)
    
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
