import requests
import time
import json
from json import JSONEncoder

from models.page import Page, Pages
from utils.utils import data_slicing
from config import config


class Bot:
    def __init__(self, name: str, password: str):
        self.name = name
        self.password = password
    

class BotEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


class BotManagement:
    def __init__(self):
        self.data: list[Bot] = self._get_data()

    def save_new_bot(self, new_bot):
        self.data.append(new_bot)
        with open(config.BOT_LOGIN_PATH, "w") as file:
            json.dump(self.data, file, indent=4, cls=BotEncoder)

    def _get_data(self) -> list:
        try:
            with open(config.BOT_LOGIN_PATH, "r") as file:
                data = [Bot(**bot_params) for bot_params in json.load(file)]
        except FileNotFoundError:
            data = []

        return data
        
    def __iter__(self):
        return iter(self.data)


class MediaWiki:
    SESSION = requests.session()
    MAX_URL_LENGTH = 8213
    MAX_PARAMS = 500
    MAX_LAG = 1

    def __init__(
        self,
        api_url: str,
        bot: Bot,
    ):
        self.api_url = api_url
        self.bot = (bot,)
        self.csrf_token = None

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

        return self.SESSION.get(url=self.api_url, params=query_params).json()

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

        result = self.SESSION.post(self.api_url, data=query_params).json()

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

        request_result = self.SESSION.post(self.api_url, data=query_params).json()

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

        request_result = self.SESSION.post(self.api_url, data=query_params).json()

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

    def change_bot(self, new_bot: Bot):
        self.bot = new_bot