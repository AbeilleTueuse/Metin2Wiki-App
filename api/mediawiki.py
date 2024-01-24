import requests
import time
import json
from json import JSONEncoder

from models.page import Page, MonsterPage
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
    def __init__(self, lang: str = "fr"):
        self.data: dict[str, list[Bot]] = self._get_data()
        self.lang = lang

    def save_new_bot(self, new_bot: Bot):
        if self.lang in self.data:
            self.data[self.lang].append(new_bot)
        else:
            self.data[self.lang] = [new_bot]
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
            self.data[self.lang].remove(bot)
            self.save()

    def get_default_bot(self):
        for bot in self:
            if bot.default:
                return bot
        return None

    def change_default_bot(self, bot_name: str):
        default_bot = None
        for bot in self:
            bot.default = 0
            if bot.name == bot_name:
                bot.default = 1
                default_bot = bot
        self.save()
        return default_bot

    def change_lang(self, new_lang: str):
        self.lang = new_lang

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

    def __iter__(self):
        data = []
        if self.lang in self.data:
            data = self.data[self.lang]
        return iter(data)

    def __len__(self):
        return sum(1 for _ in self)


class MediaWiki:
    MAX_URL_LENGTH = 8213
    MAX_PARAMS = 500
    MAX_LAG = 1
    LIST_TO_PREFIX = {
        "categorymembers": "cm",
        "allimages": "ai",
        "allpages": "ap",
    }

    def __init__(
        self,
        api_url: str,
        bot: Bot = None,
    ):
        self.api_url = api_url
        self.bot = bot
        self.csrf_token = None
        self.session = self._new_session()
        self.logged = False

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

        if self.logged:
            return

        if self.bot is None:
            raise ValueError("Add a bot before login.")

        query_params = {
            "action": "login",
            "lgname": self.bot.name,
            "lgpassword": self.bot.password,
            "lgtoken": get_login_token(),
            "format": "json",
        }

        result = self.wiki_post(query_params)
        login_result = result["login"]["result"]

        if login_result == "Failed":
            raise ConnectionError(result["login"]["reason"])
        elif login_result == "Success":
            self.logged = True

    def logout(self):
        if not self.logged:
            return

        query_params = {
            "action": "logout",
            "token": self.get_csrf_token(),
            "format": "json",
        }

        result = self.wiki_post(query_params)

        if not "error" in result:
            self.logged = False

    def get_csrf_token(self) -> str:
        if self.csrf_token is not None:
            return self.csrf_token

        query_params = {
            "action": "query",
            "meta": "tokens",
            "format": "json",
        }

        request_result = self.wiki_request(query_params)
        csrf_token = request_result["query"]["tokens"]["csrftoken"]
        self.csrf_token = csrf_token

        return csrf_token

    def query_request_recursive(self, query_params, result: list) -> list[dict]:
        request_result = self.wiki_request(query_params)
        continue_value = request_result.get("continue", False)
        list_value = query_params["list"]

        result += request_result["query"][list_value]

        if continue_value:
            prefix = self.LIST_TO_PREFIX[list_value] + "continue"
            query_params[prefix] = continue_value[prefix]
            self.query_request_recursive(query_params, result)

        return result
    
    def pages(self, pages: list[dict], category: str):
        if category == "monster":
            return [MonsterPage(page) for page in pages]
        return [Page(page) for page in pages]

    def category(self, category: str, exclude_category: str = None):
        query_params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": "max",
            "cmtype": "page",
        }

        pages = self.query_request_recursive(query_params, [])

        if exclude_category is not None:
            pages_to_exclude = self.category(exclude_category)
            pages = [page for page in pages if page not in pages_to_exclude]

        return pages

    def edit(self, page: Page, summary=""):
        query_params = {
            "action": "edit",
            "pageid": page.pageid,
            "token": self.get_csrf_token(),
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

        self.login()

        query_params = {
            "action": "delete",
            "token": self.get_csrf_token(),
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
                raise PermissionError(request_result["error"]["info"])

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

        return self.to_page_list(pages)

    def all_images(self):
        query_params = {
            "action": "query",
            "list": "allpages",
            "apnamespace": 6,
            "aplimit": "max",
            "format": "json",
        }

        pages = self.query_request_recursive(query_params, [])
        return self.to_page_list(pages)

    def empty_images(self):
        pages = self.pages(self.all_images())
        pages = pages.filter_by()
        return pages

    def get_content(self, pages: list[dict]) -> list[dict]:
        pages_with_content = []
        for pages_slice in data_slicing(pages, self.MAX_PARAMS):
                pages_with_content += self._get_content_limited(pages_slice)

        return pages_with_content

    def _get_content_limited(self, pages: list[dict]) -> list[dict]:
        if len(pages) > self.MAX_PARAMS:
            raise ValueError(f"Number of pages must be inferior to {self.MAX_PARAMS}")

        query_params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "rvprop": "content",
            "formatversion": "2",
            "pageids": "|".join(str(page["pageid"]) for page in pages),
        }

        request_result = self.wiki_request(query_params)

        return request_result["query"]["pages"]
    
    def get_image_urls(self, image_name: str):
        query_params = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "titles": image_name,
            "iiprop": "url",
        }

        request_result = self.wiki_request(query_params)

        pages_info: dict = request_result["query"]["pages"]

        return pages_info