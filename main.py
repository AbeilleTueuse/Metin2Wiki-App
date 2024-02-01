from api.metin2wiki import Metin2Wiki
from models.page import Page
from UI.graphic import WikiApp


if __name__ == "__main__":
    # wiki_app = WikiApp()
    # wiki_app.mainloop()
    # Page.new_page(
    #     category="mob",
    #     vnum=101,
    #     localisation="I",
    #     zone="[[Repaire de Meley]]"
    #     )

    metin2wiki = Metin2Wiki()
    metin2wiki.login()
    page = metin2wiki.page(title="Prince Ochao")
    page.update_links()