from api.mediawiki import MediaWiki


class Metin2Wiki(MediaWiki):


    ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
    ALPHABET += ALPHABET.upper()
    BASE = len(ALPHABET)


    def __init__(
            self,
            lang = 'fr',
            bot_name: str | None = None,
            bot_password: str | None = None
            ):

        super().__init__(
            api_url = f'https://{lang}-wiki.metin2.gameforge.com/api.php',
            bot_name = bot_name,
            bot_password = bot_password
        )


    def vnum_conversion(self, number: int):

        if number == 0:
            return 'a'
        
        converted_number = ''
        
        while number > 0:
            number, remainder = divmod(number, self.BASE)
            converted_number += self.ALPHABET[remainder]
        
        return converted_number
    

    def code_to_vnum(self, letters: str) -> int:

        number = 0

        for i, letter in enumerate(letters):
            value = self.ALPHABET.index(letter)
            number += value * (self.BASE ** i)
        
        return number




class Bot:
    def __init__(
        self,
        name: str | None = None,
        password: str | None = None,
    ):
        self.name = name
        self.password = password


class BotManaging:
    def __init__(self):
        pass

    def check_bot(self, name: str, password: str):
        
        metin2wiki = Metin2Wiki(bot_name=name, bot_password=password)
        metin2wiki.login()
