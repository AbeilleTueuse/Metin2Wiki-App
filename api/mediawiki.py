import requests
import time
import json
from json import JSONEncoder

from models.page import Page, Pages
from utils.utils import data_slicing
from config import config


class Bot:
    def __init__(self, name: str, password: str, default: int = 0):
        self.name = name
        self.password = password
        self.default = default

    def __eq__(self, other):
        if not isinstance(other, Bot):
            return False
        return other.name == self.name

    def __str__(self):
        return f"(Bot: {self.name})"


class BotEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


class BotManagement:
    def __init__(self, metin2wiki):
        self.data: dict[str, list[Bot]] = self._get_data()
        self.metin2wiki = metin2wiki

    def save_new_bot(self, new_bot: Bot):
        current_lang = self._current_lang()
        if current_lang in self.data:
            self.data[current_lang].append(new_bot)
        else:
            self.data[current_lang] = [new_bot]
        self.save()

    def save(self):
        with open(config.BOT_LOGIN_PATH, "w") as file:
            json.dump(self.data, file, indent=4, cls=BotEncoder)

    def has(self, bot: Bot):
        for saved_bot in self:
            if bot == saved_bot:
                return True
        return False

    def delete(self, bot: Bot):
        if self.has(bot):
            current_lang = self._current_lang()
            self.data[current_lang].remove(bot)
            self.save()

    def set_default_bot(self):
        for bot in self:
            if bot.default:
                self.metin2wiki.set_bot(bot)
                return bot.name
        return ""

    def change_default_bot(self, bot_name: str):
        for bot in self:
            bot.default = 0
            if bot.name == bot_name:
                self.metin2wiki.set_bot(bot)
                bot.default = 1
        self.save()

    def _get_data(self) -> list:
        try:
            with open(config.BOT_LOGIN_PATH, "r") as file:
                data = json.load(file)
                data = {
                    lang: [Bot(**bot_params) for bot_params in data[lang]]
                    for lang in data
                }
        except FileNotFoundError:
            data = {}

        return data

    def _current_lang(self):
        return self.metin2wiki.lang

    def __iter__(self):
        current_lang = self._current_lang()
        data = []
        if current_lang in self.data:
            data = self.data[current_lang]
        return iter(data)

    def __len__(self):
        return sum(1 for _ in self)


class MediaWiki:
    MAX_URL_LENGTH = 8213
    MAX_PARAMS = 500
    MAX_LAG = 1

    def __init__(
        self,
        api_url: str,
        bot: Bot,
    ):
        self.api_url = api_url
        self.bot = bot
        self.csrf_token = None
        self.session = self._new_session()

    def set_bot(self, bot: Bot):
        self.bot = bot
        self.csrf_token = None
        self.session.close()
        self.session = self._new_session()

    def _new_session(self):
        return requests.session()

    def _check_params(self, params: list | None, type_: str):
        def check_type_names(el):
            if isinstance(el, Page):
                return el.title
            return el

        def check_type_ids(el):
            if isinstance(el, Page):
                return el.pageid
            elif isinstance(el, str):
                raise ValueError(f"{el} isn't an integer")
            return el

        if params is None:
            return

        if type_ == "names":
            params = map(check_type_names, params)
        elif type_ == "ids":
            params = map(check_type_ids, params)

        return data_slicing(params, self.MAX_PARAMS)

    def wiki_request(self, query_params: dict) -> dict:
        query_params["maxlag"] = self.MAX_LAG
        return self.session.get(url=self.api_url, params=query_params).json()

    def wiki_post(self, query_params: dict) -> dict:
        return self.session.post(self.api_url, data=query_params).json()

    def login(self):
        def get_login_token():
            query_params = {
                "action": "query",
                "meta": "tokens",
                "type": "login",
                "format": "json",
            }

            request_result = self.wiki_request(query_params)

            return request_result["query"]["tokens"]["logintoken"]

        query_params = {
            "action": "login",
            "lgname": self.bot.name,
            "lgpassword": self.bot.password,
            "lgtoken": get_login_token(),
            "format": "json",
        }

        result = self.wiki_post(query_params)

        if result["login"]["result"] == "Failed":
            raise ConnectionError(result["login"]["reason"])

    def get_csrf_token(self) -> str:
        query_params = {
            "action": "query",
            "meta": "tokens",
            "format": "json",
        }

        request_result = self.wiki_request(query_params)

        return request_result["query"]["tokens"]["csrftoken"]

    def page(self, title: str | None = None, pageid: int | None = None):
        return Page(self, title=title, pageid=pageid)

    def pages(self, data: list[int] | list[Page]):
        return Pages(self, data)

    def category(self, category: str):
        query_params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": "max",
            "cmtype": "page",
        }

        def request(query_params, pages):
            request_result = self.wiki_request(query_params)

            cmcontinue = request_result.get("continue", False)

            pages += request_result["query"]["categorymembers"]

            if cmcontinue:
                query_params["cmcontinue"] = cmcontinue["cmcontinue"]
                request(query_params, pages)

            return pages

        pages = request(query_params, [])

        return [Page(self, page["title"], page["pageid"]) for page in pages]

    def edit(self, page: Page, summary=""):
        if self.csrf_token is None:
            self.csrf_token = self.get_csrf_token()

        query_params = {
            "action": "edit",
            "pageid": page.pageid,
            "token": self.csrf_token,
            "format": "json",
            "bot": "true",
            "minor": "true",
            "summary": summary,
            "text": str(page.content),
        }

        request_result = self.wiki_post(query_params)

        if "error" in request_result:
            if request_result["error"]["code"] == "ratelimited":
                time.sleep(5)
                self.edit(page=page, summary=summary)

        print(f"{page.title} modified.")

    def delete(self, page: Page, reason=""):
        if len(page.backlinks) != 0:
            print(f"Page {page.title} has {len(page.backlinks)} backlinks.")
            return

        if self.csrf_token is None:
            self.csrf_token = self.get_csrf_token()

        query_params = {
            "action": "delete",
            "token": self.csrf_token,
            "format": "json",
            "reason": reason,
        }

        if page.pageid is not None:
            query_params["pageid"] = page.pageid
        elif page.title is not None:
            query_params["title"] = page.title
        else:
            raise ValueError("Page must have pageid or title attribute.")

        request_result = self.wiki_post(query_params)

        if "error" in request_result:
            if request_result["error"]["code"] == "permissiondenied":
                print(request_result["error"]["info"])

        else:
            print(f"{page.title} deleted.")

    def short_pages(self):
        query_params = {
            "action": "query",
            "format": "json",
            "list": "allpages",
            "aplimit": "500",
            "apmaxsize": "0",
        }

        request_result = self.wiki_request(query_params)

        pages = request_result["query"]["allpages"]

        return [Page(self, page["title"], page["pageid"]) for page in pages]
