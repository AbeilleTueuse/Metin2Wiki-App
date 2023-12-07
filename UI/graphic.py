import tkinter as tk
from tkinter.messagebox import showinfo
import customtkinter as ctk
from datetime import datetime

from config import config
from UI.settings import Settings
from api.metin2wiki import Metin2Wiki
from api.mediawiki import Bot

ctk.set_appearance_mode("dark")

MENU_STYLE = {
    "tearoff": 0,
    "background": "gray90",
    "activebackground": "darkorange",
}
HEADER_LABEL_STYLE = {
    "font": ("Helvetica", 12, "bold"),
    "background": "#3498db",
    "foreground": "white",
    "padx": 5,
    "pady": 5,
}
TABLE_ROW_STYLE = {"background": "#B0C4DE", "borderwidth": 2, "relief": "solid"}

TITLE = "Metin2Wiki App"
VERSION = "v0.1"
YEAR = 2023
CREATOR = "ArcMeurtrier/Ankhseram"
DIMENSION = "800x600"


class WikiApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(TITLE)
        self.geometry(DIMENSION)
        self.iconbitmap(config.FAVIVON_PATH)

        # self.defaultFont = font.nametofont("TkDefaultFont")
        # self.defaultFont.configure(size=12)

        self.grid_rowconfigure(0, weight=5, minsize=200)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_frames()

    def create_frames(self):
        self.settings = Settings()
        self.metin2wiki = Metin2Wiki(lang=self.settings["lang"])

        self.console_frame = ConsoleFrame(self)
        self.console_frame.grid(row=1, column=0, sticky="nswe")

        self.main_frame = MainFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nswe")

        self.menu_bar = MenuBar(self, self.main_frame)
        self.config(menu=self.menu_bar)

    def delete_frames(self):
        for child in self.winfo_children():
            child.destroy()

    def change_settings(self, key, value):
        self.settings[key] = value
        self.settings.save_settings()

    def _switch_frame(self, frame: ctk.CTkScrollableFrame):
        self.main_frame.current_frame.grid_forget()
        frame.grid(row=0, column=0, sticky="nswe")
        self.main_frame.current_frame = frame
        self.console_frame.write(f"Switching to {frame.NAME.lower()}.")


class WikiAppMixin:
    def __init__(self, wiki_app: WikiApp):
        self.wiki_app = wiki_app
        self.console_frame = wiki_app.console_frame
        self.metin2wiki = wiki_app.metin2wiki

    def write_in_console(self, *text):
        self.console_frame.write(*text)


class MainFrame(ctk.CTkFrame):
    def __init__(self, master: WikiApp):
        ctk.CTkFrame.__init__(self, master)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.default_frame = DefaultFrame(self)
        self.default_frame.grid(row=0, column=0, sticky="nswe")

        self.current_frame = self.default_frame

        self.bot_managing_frame = BotManagingFrame(self, master)
        self.short_pages_frame = ShortPagesFrame(self, master)
        self.empty_images_frame = EmptyImagesFrame(self, master)


class MenuBar(tk.Menu, WikiAppMixin):
    def __init__(self, master: WikiApp, main_frame: MainFrame):
        tk.Menu.__init__(self, master)
        WikiAppMixin.__init__(self, master)

        self.main_frame = main_frame
        self.default_lang = master.settings["lang"]
        self.language_var = ctk.StringVar()
        self.language_var.set(self.default_lang)
        self.write_in_console(
            f"Default language: {self.default_lang}. Can be changed in Settings > Wiki language."
        )

        self._create_file()
        self._create_tool()
        self._create_settings()
        self._create_about_us()

    def _create_menu(self, menu_name):
        menu_button = tk.Menubutton(self, text=menu_name)
        menu_button.pack(side=tk.LEFT)

        menu = tk.Menu(menu_button, **MENU_STYLE)
        menu_button.configure(menu=menu)

        return menu

    def _create_file(self):
        menu = tk.Menu(self, **MENU_STYLE)
        menu.add_command(label="Quit", command=quit)
        self.add_cascade(label="File", menu=menu)

    def _create_tool(self):
        menu = tk.Menu(self, **MENU_STYLE)
        menu.add_command(
            label="Short pages",
            command=lambda: self.wiki_app._switch_frame(
                self.wiki_app.main_frame.short_pages_frame
            ),
        )
        menu.add_command(
            label="Empty images",
            command=lambda: self.wiki_app._switch_frame(
                self.wiki_app.main_frame.empty_images_frame
            ),
        )
        self.add_cascade(label="Tools", menu=menu)

    def _create_settings(self):
        menu = tk.Menu(self, **MENU_STYLE)
        lang_menu = tk.Menu(menu, **MENU_STYLE)

        for lang in self.metin2wiki.ALL_LANG:
            lang_menu.add_radiobutton(
                label=lang,
                value=lang,
                variable=self.language_var,
                command=self._on_language_change,
            )

        menu.add_cascade(label="Wiki language", menu=lang_menu)
        menu.add_command(
            label="Bot managing",
            command=lambda: self.wiki_app._switch_frame(
                self.wiki_app.main_frame.bot_managing_frame
            ),
        )
        self.add_cascade(label="Settings", menu=menu)

    def _on_language_change(self):
        new_lang = self.language_var.get()
        if new_lang != self.default_lang:
            self.wiki_app.metin2wiki.logout()
            self.wiki_app.metin2wiki.session.close()
            self.wiki_app.change_settings("lang", new_lang)
            self.wiki_app.delete_frames()
            self.wiki_app.create_frames()

    def _create_about_us(self):
        file = tk.Menu(self, **MENU_STYLE)
        file.add_command(label="About", command=self._about_us)
        self.add_cascade(label="Help", menu=file)

    def _about_us(self):
        showinfo(
            title="About",
            message="\n".join([f"{TITLE} {VERSION}", f"{YEAR}", f"{CREATOR}"]),
        )


class DefaultFrame(ctk.CTkScrollableFrame):
    def __init__(self, master):
        ctk.CTkScrollableFrame.__init__(self, master)
        self.label = ctk.CTkLabel(self, text="Default frame")
        self.label.pack(pady=10)


class ConsoleFrame(ctk.CTkFrame):
    def __init__(self, master: WikiApp):
        ctk.CTkFrame.__init__(self, master)

        title_label = ctk.CTkLabel(
            self, text="Console"
        )
        title_label.pack(fill=tk.BOTH)

        self.console_text = ctk.CTkTextbox(
            self,
            wrap="word",
        )
        self.console_text.pack(fill=tk.BOTH, expand=True)

    def write(self, *text):
        for msg in text:
            time = datetime.now().strftime("%H:%M")
            self.console_text.insert(tk.END, f"{time}: {msg}\n")
            self.console_text.see(tk.END)


class BotManagingFrame(ctk.CTkScrollableFrame, WikiAppMixin):
    NAME = "Bot managing"
    TABLE_COLUMNS = [
        "Bot name",
        "Bot password",
        "Check",
        "Permissions",
        "Use",
        "Delete",
    ]

    def __init__(self, master: MainFrame, wiki_app: WikiApp):
        ctk.CTkScrollableFrame.__init__(self, master)
        WikiAppMixin.__init__(self, wiki_app)

        self.default_bot_name = self.metin2wiki.set_default_bot()
        self.bot_var = ctk.StringVar()
        self.bot_var.set(self.default_bot_name)
        self._initial_message()
        self._table_initialisation()
        self.add_saved_bots()

    def _initial_message(self):
        number_of_bots = self.metin2wiki.get_number_of_bots()
        if number_of_bots:
            if self.default_bot_name is None:
                message = f"{number_of_bots} bot(s) are saved. No default bot is selected. Can be changed in Settings > Bot managing."
            else:
                message = f"{number_of_bots} bot(s) are saved. Default bot is: {self.default_bot_name}. Can be changed in Settings > Bot managing."

            self.write_in_console(message)
        else:
            self.write_in_console(
                "No saved bot. To add a new bot: Settings > Bot managing"
            )

    def _table_initialisation(self):
        for index, name in enumerate(self.TABLE_COLUMNS):
            self.columnconfigure(index, weight=1)
            label = ctk.CTkLabel(self, text=name)
            label.grid(row=0, column=index, sticky="nsew")

    def reset_table(self):
        for widget in self.winfo_children()[len(self.TABLE_COLUMNS) :]:
            widget.destroy()

    def add_saved_bots(self):
        index = 0
        for index, bot in enumerate(self.metin2wiki.bot_management):
            index += 1
            self._add_bot(bot, index)

        self.add_bot_button = ctk.CTkButton(
            self,
            text="Add new bot",
            command=self._new_bot_window,
        )
        self.add_bot_button.grid(
            row=index + 1, columnspan=len(self.TABLE_COLUMNS), sticky="nsew"
        )

    def _add_bot(self, bot: Bot, index: int):
        label_name = ctk.CTkLabel(self, text=bot.name)
        label_name.grid(row=index, column=0, sticky="nsew")
        label_password = ctk.CTkLabel(self, text=bot.password)
        label_password.grid(row=index, column=1, sticky="nsew")
        label_validation = ctk.CTkLabel(self, text="✔️")
        label_validation.grid(row=index, column=2, sticky="nsew")
        button_use = ctk.CTkRadioButton(
            self,
            value=bot.name,
            variable=self.bot_var,
            command=self._handle_default_bot,
        )
        button_use.grid(row=index, column=4, sticky="nsew")
        button_delete = ctk.CTkButton(
            self, text="🗑️", command=lambda: self._delete_bot(bot)
        )
        button_delete.grid(row=index, column=5, sticky="nsew")

    def _add_new_bot(self, new_bot: Bot):
        index = self.add_bot_button.grid_info()["row"]
        self._add_bot(new_bot, index)
        self.add_bot_button.grid(row=index + 1)

    def _delete_bot(self, bot: Bot):
        self.metin2wiki.bot_management.delete(bot)
        self.write_in_console(f"The bot {bot.name} was deleted.")

        if bot.name == self.default_bot_name:
            self.bot_var.set(None)
            self._handle_default_bot()

        self.reset_table()
        self.add_saved_bots()

    def _new_bot_window(self):
        new_bot_window = ctk.CTkToplevel(self.master)
        new_bot_window.title("Add new bot")

        label_name = ctk.CTkLabel(new_bot_window, text="Bot name:")
        label_name.grid(row=0, column=0, sticky="e")
        
        entry_name = ctk.CTkEntry(new_bot_window)
        entry_name.grid(row=0, column=1)

        label_password = ctk.CTkLabel(new_bot_window, text="Bot password:")
        label_password.grid(row=1, column=0, sticky="e")

        entry_password = ctk.CTkEntry(new_bot_window)
        entry_password.grid(row=1, column=1)

        check_button = ctk.CTkButton(
            new_bot_window,
            text="Check login",
            command=lambda: self._check_login(entry_name, entry_password),
        )
        check_button.grid(row=2, columnspan=2, sticky="nsew", padx=5, pady=5)

    def _handle_default_bot(self):
        new_default_bot_name = self.bot_var.get()

        if self.default_bot_name == new_default_bot_name:
            return

        self.default_bot_name = new_default_bot_name

        if new_default_bot_name == "None":
            self.metin2wiki.delete_bot()
            self.write_in_console(f"No default bot is selected.")
        else:
            self.write_in_console(f"Default bot is now set to {new_default_bot_name}.")
            self.metin2wiki.change_default_bot(new_default_bot_name)

    def _check_login(self, entry_name: ctk.CTkEntry, entry_password: ctk.CTkEntry):
        bot_name = entry_name.get()
        bot_password = entry_password.get()

        if not (bot_name and bot_password):
            self.write_in_console(
                f"Please enter a bot name and a bot password before checking."
            )
            return

        new_bot = Bot(name=bot_name, password=bot_password)

        if self.metin2wiki.bot_management.has(new_bot):
            self.write_in_console(f"The bot {bot_name} is already added.")
            return

        self.write_in_console(
            f"Trying connexion to Metin2Wiki with the bot {bot_name}..."
        )

        self.wiki_app.metin2wiki.logout()
        self.wiki_app.metin2wiki.set_bot(bot=new_bot)
        try:
            self.wiki_app.metin2wiki.login()
        except ConnectionError as err:
            self.write_in_console(err)
        else:
            self.write_in_console(f"Sucess! The bot {bot_name} is now saved.")
            self.metin2wiki.bot_management.save_new_bot(new_bot=new_bot)
            self._add_new_bot(new_bot=new_bot)
            self.bot_var.set(new_bot.name)
            self._handle_default_bot()


class ShortPagesFrame(ctk.CTkScrollableFrame, WikiAppMixin):
    NAME = "Short pages tool"

    def __init__(self, master: MainFrame, wiki_app: WikiApp):
        ctk.CTkScrollableFrame.__init__(self, master)
        WikiAppMixin.__init__(self, wiki_app)

        title_label = ctk.CTkLabel(self, text=self.NAME)
        title_label.pack(pady=10)

        self._add_search_button()

    def _add_search_button(self):
        button = ctk.CTkButton(self, text="Search empty pages", command=self._run_tool)
        button.pack(fill=tk.X)

    def _create_table(self, short_pages):
        for page in short_pages:
            page_frame = ctk.CTkFrame(self)
            page_title = ctk.CTkTextbox(page_frame, height=1, width=20, wrap=tk.WORD)
            page_title.insert(tk.INSERT, page.title)
            page_title.configure(state="disabled")
            page_title.grid(row=0, column=0, sticky="we")

            delete_button = ctk.CTkButton(
                page_frame,
                text="Delete 🗑️",
                command=lambda: self._delete_page(page_frame, page),
            )
            delete_button.grid(row=0, column=1, sticky="we")
            page_frame.columnconfigure(0, weight=10)
            page_frame.columnconfigure(1, weight=1)
            page_frame.pack(fill=tk.X)

        delete_all_button = ctk.CTkButton(
            self,
            text="Delete all",
            command=self._delete_all_pages,
        )
        delete_all_button.pack(fill=tk.BOTH, pady=10)

    def _run_tool(self):
        self.write_in_console("Run tool...")
        self.wiki_app.metin2wiki.login()
        short_pages = self.metin2wiki.short_pages()
        self.write_in_console(f"{len(short_pages)} short page(s) found.")
        self._create_table(short_pages)


    def _delete_page(self, page_frame: ctk.CTkFrame, page):
        try:
            page.delete("Page without any content")
        except PermissionError:
            self.write_in_console(
                f"You don't have the permission to delete the page {page.title}."
            )
        else:
            self.write_in_console(f"The page {page.title} was successfully deleted.")
            page_frame.destroy()
            self.short_pages.remove(page)

    def _delete_all_pages(self):
        self.write_in_console("Delete all button isn't implemented yet.")


class EmptyImagesFrame(ctk.CTkScrollableFrame, WikiAppMixin):
    NAME = "Empty images tool"

    def __init__(self, master: MainFrame, wiki_app: WikiApp):
        ctk.CTkScrollableFrame.__init__(self, master)
        WikiAppMixin.__init__(self, wiki_app)

        title_label = ctk.CTkLabel(self, text=self.NAME, font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)
        self._add_search_button()

    def _add_search_button(self):
        button = ctk.CTkButton(self, text="Search empty images", command=self._run_tool)
        button.pack(fill=tk.X)

    def _create_table(self, empty_pages):
        for page in empty_pages:
            page_frame = PageFrame(page, self, self.wiki_app)
            page_frame.pack(fill=tk.X)

    def _run_tool(self):
        self.write_in_console("Run tool...")
        self.wiki_app.metin2wiki.login()
        empty_pages = self.wiki_app.metin2wiki.empty_images()
        self.write_in_console(f"{len(empty_pages)} empty image(s) found.")
        self._create_table(empty_pages)


class PageFrame(ctk.CTkFrame, WikiAppMixin):
    def __init__(self, page, master, wiki_app: WikiApp):
        ctk.CTkFrame.__init__(self, master, padx=10, pady=10)
        WikiAppMixin.__init__(self, wiki_app)
        
        page_title = ctk.CTkTextbox(self, height=1, width=20, wrap=tk.WORD)
        page_title.insert(tk.INSERT, page.title)
        page_title.configure(state="disabled")
        page_title.grid(row=0, column=0, sticky="we")