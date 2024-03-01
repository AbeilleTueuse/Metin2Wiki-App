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
    metin2wiki.save_data_for_calculator()