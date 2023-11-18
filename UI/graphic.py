# %%
import tkinter as tk
from tkinter.simpledialog import askstring
from tkinter.messagebox import showinfo
import tkinter.filedialog as fd
from datetime import datetime

from config import config
from UI.settings import Settings
from api.metin2wiki import Metin2Wiki
from api.mediawiki import BotManagement, Bot

BUTTON_STYLE = {"padx": 10, "pady": 5, "activebackground": "darkorange"}
BUTTON_ADD_STYLE = {
    "background": "#4CAF50",
    "foreground": "white",
    "font": ("Helvetica", 12, "bold"),
    "relief": tk.RAISED,
}
MENU_STYLE = {
    "tearoff": 0,
    "background": "gray90",
    "activebackground": "darkorange",
}
HEADER_LABEL = {
    "font": ("Helvetica", 12, "bold"),
    "background": "#3498db",
    "foreground": "white",
    "padx": 5,
    "pady": 5,
}

TITLE = "Metin2Wiki App"
VERSION = "v0.1"
YEAR = 2023
CREATOR = "ArcMeurtrier/Ankhseram"
DIMENSION = "800x600"

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


class WikiApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(TITLE)
        self.geometry(DIMENSION)
        self.iconbitmap(config.FAVIVON_PATH)

        self.settings = Settings()
        self.metin2wiki = Metin2Wiki(lang=self.settings["lang"])

        self.console_frame = ConsoleFrame(self)
        self.console_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=False)

        self.main_frame = MainFrame(self)
        self.main_frame.pack(fill=tk.BOTH)

        self.menu_bar = MenuBar(self, self.main_frame)
        self.config(menu=self.menu_bar)


    def change_settings(self, key, value):
        self.settings[key] = value
        self.settings.save_settings()

    def _switch_frame(self, frame: tk.Frame):
        self.main_frame.current_frame.pack_forget()
        frame.pack(fill=tk.BOTH)
        self.main_frame.current_frame = frame


class MainFrame(tk.Frame):
    def __init__(self, master: WikiApp):
        tk.Frame.__init__(self, master)

        self.default_frame = DefaultFrame(self)
        self.default_frame.pack(fill=tk.BOTH)

        self.current_frame = self.default_frame

        self.bot_managing_frame = BotManagingFrame(self, master)


class MenuBar(tk.Menu):
    def __init__(self, master: WikiApp, main_frame: MainFrame):
        tk.Menu.__init__(self, master)

        self.wiki_app = master
        self.console_frame = master.console_frame
        self.main_frame = main_frame

        self.default_lang = master.settings["lang"]
        self.language_var = tk.StringVar()
        self.language_var.set(self.default_lang)
        self.write(
            f"Default language: {self.default_lang}. Can be changed in Settings > Wiki language."
        )

        self._create_file_menu()
        self._create_settings()
        self._create_about_us()

    def _create_menu(self, menu_name):
        menu_button = tk.Menubutton(self, text=menu_name, **BUTTON_STYLE)
        menu_button.pack(side=tk.LEFT)

        menu = tk.Menu(menu_button, **MENU_STYLE)
        menu_button.configure(menu=menu)

        return menu

    def _create_file_menu(self):
        file = tk.Menu(self, **MENU_STYLE)
        file.add_command(label="Quit", command=quit)
        self.add_cascade(label="File", menu=file)

    def _create_settings(self):
        file = tk.Menu(self, **MENU_STYLE)
        lang_menu = tk.Menu(file, **MENU_STYLE)

        for lang in ALL_LANG:
            lang_menu.add_radiobutton(
                label=lang,
                value=lang,
                variable=self.language_var,
                command=self._on_language_change,
            )

        file.add_cascade(label="Wiki language", menu=lang_menu)
        file.add_command(
            label="Bot managing",
            command=lambda: self.wiki_app._switch_frame(
                self.wiki_app.main_frame.bot_managing_frame
            ),
        )
        self.add_cascade(label="Settings", menu=file)

    def _on_language_change(self):
        new_lang = self.language_var.get()
        if new_lang != self.default_lang:
            self.wiki_app.change_settings("lang", new_lang)
            self.wiki_app.metin2wiki.change_lang(new_lang)
            self.write(f"Language modification: {self.default_lang} to {new_lang}.")
            self.default_lang = new_lang
            self.main_frame.bot_managing_frame.reset_table()
            self.main_frame.bot_managing_frame.add_saved_bots()

    def _create_about_us(self):
        file = tk.Menu(self, **MENU_STYLE)
        file.add_command(label="About", command=self._about_us)
        self.add_cascade(label="Help", menu=file)

    def _about_us(self):
        showinfo(
            title="About",
            message="\n".join([f"{TITLE} {VERSION}", f"{YEAR}", f"{CREATOR}"]),
        )

    def write(self, text):
        self.console_frame.write(text)


class DefaultFrame(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.label = tk.Label(self, text="Default frame")
        self.label.pack(pady=10)


class ConsoleFrame(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        title_label = tk.Label(
            self, text="Console", font=("Helvetica", 14, "bold"), background="lightgray"
        )
        title_label.pack(fill=tk.BOTH)

        self.console_text = tk.Text(
            self,
            wrap="word",
            font=("Courier", 12),
            background="black",
            foreground="white",
            height=10
        )
        self.console_text.pack(fill=tk.BOTH, expand=True)

    def write(self, text):
        time = datetime.now().strftime("%H:%M")
        self.console_text.insert(tk.END, f"{time}: {text}\n")
        self.console_text.see(tk.END)


class BotManagingFrame(tk.Frame):
    TABLE_COLUMNS = ["Bot name", "Bot password", "Check", "Permissions", "Delete"]

    def __init__(self, master: MainFrame, wiki_app: WikiApp):
        tk.Frame.__init__(self, master)

        self.wiki_app = wiki_app
        self.console_frame = wiki_app.console_frame
        self.metin2wiki = wiki_app.metin2wiki
        self.bot_management = BotManagement(metin2wiki=self.metin2wiki)
        self.table: list[tk.Button] = []
        self._table_initialisation()
        self.add_saved_bots()

    def _table_initialisation(self):
        for index, name in enumerate(self.TABLE_COLUMNS):
            self.columnconfigure(index, weight=1)
            label = tk.Label(self, text=name, **HEADER_LABEL)
            label.grid(row=0, column=index, sticky="nsew")

    def reset_table(self):
        for widget in self.winfo_children()[len(self.TABLE_COLUMNS):]:
            widget.destroy()

    def add_saved_bots(self):
        index = 0
        for index, bot in enumerate(self.bot_management):
            index += 1
            self._add_bot(bot, index)

        self.add_bot_button = tk.Button(
            self,
            text="Add new bot",
            **BUTTON_STYLE,
            **BUTTON_ADD_STYLE,
            command=self._new_bot_window,
        )
        self.add_bot_button.grid(row=index + 1, columnspan=len(self.TABLE_COLUMNS), sticky="nsew")

    def _add_bot(self, bot: Bot, index: int):
        label_name = tk.Label(self, text=bot.name)
        label_name.grid(row=index, column=0, sticky="nsew")
        label_password = tk.Label(self, text=bot.password)
        label_password.grid(row=index, column=1, sticky="nsew")
        label_validation = tk.Label(self, text="✔️", fg="green")
        label_validation.grid(row=index, column=2, sticky="nsew")
        delete_button = tk.Button(self, text="🗑️", fg="red", command=lambda: self._delete_bot(bot))
        delete_button.grid(row=index, column=4, sticky="nsew")

    def _add_new_bot(self, new_bot: Bot):
        index = self.add_bot_button.grid_info()["row"]
        self._add_bot(new_bot, index)
        self.add_bot_button.grid(row=index + 1)

    def _delete_bot(self, bot: Bot):
        self.bot_management.delete(bot)
        self.reset_table()
        self.add_saved_bots()
        self.write(f"The bot {bot.name} was deleted.")

    def _new_bot_window(self):
        new_bot_window = tk.Toplevel(self.master, padx=10, pady=10)
        new_bot_window.title("Add new bot")

        label_name = tk.Label(new_bot_window, text="Bot name:")
        label_name.grid(row=0, column=0, sticky="e")

        entry_name = tk.Entry(new_bot_window)
        entry_name.grid(row=0, column=1)

        label_password = tk.Label(new_bot_window, text="Bot password:")
        label_password.grid(row=1, column=0, sticky="e")

        entry_password = tk.Entry(new_bot_window)
        entry_password.grid(row=1, column=1)

        check_button = tk.Button(
            new_bot_window,
            text="Check login",
            **BUTTON_STYLE,
            **BUTTON_ADD_STYLE,
            command=lambda: self._check_login(entry_name, entry_password),
        )
        check_button.grid(row=2, columnspan=2, sticky="nsew", padx=5, pady=5)

    def _check_login(self, entry_name: tk.Entry, entry_password: tk.Entry):
        bot_name = entry_name.get()
        bot_password = entry_password.get()

        if not (bot_name and bot_password):
            self.write(f"Please enter a bot name and a bot password before checking.")
            return
        
        new_bot = Bot(name=bot_name, password=bot_password)
        
        if self.bot_management.has(new_bot):
            self.write(f"The bot {bot_name} is already added.")
            return

        self.write(f"Trying connexion to Metin2Wiki with the bot {bot_name}...")
        
        self.wiki_app.metin2wiki.change_bot(new_bot=new_bot)
        try:
            self.wiki_app.metin2wiki.login()
        except ConnectionError as err:
            self.write(err)
        else:
            self.write(f"Sucess! The bot {bot_name} is now saved.")
            self.bot_management.save_new_bot(new_bot=new_bot)
            self._add_new_bot(new_bot=new_bot)

    def write(self, text):
        self.console_frame.write(text)
