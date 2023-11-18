from api.metin2wiki import Metin2Wiki
from config import config

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

    def add_new_bot(self, name: str, password: str):
        if not isinstance(name, str):
            raise ValueError(f"The bot name should be a string.")

        if not isinstance(password, str):
            raise ValueError(f"The bot password should be a string.")
        
        metin2wiki = Metin2Wiki(bot_name=name, bot_password=password)
        metin2wiki.login()

        

        
