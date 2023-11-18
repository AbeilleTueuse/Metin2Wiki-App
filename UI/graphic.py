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
DIMENSION = "600x600"

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

        self.console_frame = ConsoleFrame(self)
        self.console_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.menu_bar = MenuBar(self)
        self.config(menu=self.menu_bar)

        self.main_frame = MainFrame(self)
        self.main_frame.pack(fill=tk.BOTH)

        self.metin2wiki = Metin2Wiki(lang=self.settings["lang"])

    def change_settings(self, key, value):
        self.settings[key] = value
        self.settings.save_settings()

    def _switch_frame(self, frame: tk.Frame):
        self.main_frame.current_frame.pack_forget()
        frame.pack(fill=tk.BOTH)
        self.main_frame.current_frame = frame


class MenuBar(tk.Menu):
    def __init__(self, master: WikiApp):
        tk.Menu.__init__(self, master)

        self.wiki_app = master
        self.console_frame = master.console_frame

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


class MainFrame(tk.Frame):
    def __init__(self, master: WikiApp):
        tk.Frame.__init__(self, master)

        self.default_frame = DefaultFrame(self)
        self.default_frame.pack(fill=tk.BOTH)

        self.current_frame = self.default_frame

        self.bot_managing_frame = BotManagingFrame(self, master)


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
        )
        self.console_text.pack(fill=tk.BOTH, expand=True)

    def write(self, text):
        time = datetime.now().strftime("%H:%M")
        self.console_text.insert(tk.END, f"{time}: {text}\n")
        self.console_text.see(tk.END)


class BotManagingFrame(tk.Frame):
    TABLE_COLUMNS = ["Bot name", "Bot password", "Check", "Permissions"]

    def __init__(self, master: MainFrame, wiki_app: WikiApp):
        tk.Frame.__init__(self, master)

        self.wiki_app = wiki_app
        self.console_frame = wiki_app.console_frame
        self.bot_management = BotManagement()
        self.table: list[tk.Button] = []
        self._table_initialisation()
        self._add_saved_bots()

    def _table_initialisation(self):
        for index, name in enumerate(self.TABLE_COLUMNS):
            self.columnconfigure(index, weight=1)
            label = tk.Label(self, text=name, **HEADER_LABEL)
            label.grid(row=0, column=index, sticky="nsew")

            # button = tk.Button(
            #     self,
            #     text="",
            #     command=lambda index=index: self._on_cell_click(row=1, column=index),
            # )
            # button.grid(row=1, column=index)

            # self.table.append(button)

    def _add_saved_bots(self):
        for index, bot in enumerate(self.bot_management):
            label_name = tk.Label(self, text=bot.name)
            label_name.grid(row=index + 1, column=0, sticky="nsew")
            label_password = tk.Label(self, text=bot.password)
            label_password.grid(row=index + 1, column=1, sticky="nsew")
            label_validation = tk.Label(self, text="✔️", fg="green")
            label_validation.grid(row=index + 1, column=2, sticky="nsew")

        add_bot = tk.Button(
            self,
            text="Add new bot",
            **BUTTON_STYLE,
            **BUTTON_ADD_STYLE,
            command=self._add_new_bot,
        )
        add_bot.grid(row=index + 2, columnspan=len(self.TABLE_COLUMNS), sticky="nsew")

    def _create_row(self):
        button = tk.Button(
            self, text="buton", command=lambda: self._on_cell_click(0, 0)
        )
        button.grid(row=1, column=0)

    def _add_new_bot(self):
        pass

    def _on_cell_click(self, row: int, column: int):
        button = self.table[column]

        if column == 0:
            user_input = askstring(
                title="Bot login", prompt="Bot name:", initialvalue=button.cget("text")
            )

            if user_input is not None:
                self.table[column].config(text=user_input)

        if column == 1:
            user_input = askstring(
                title="Bot login",
                prompt="Bot password:",
                initialvalue=button.cget("text"),
            )

            if user_input is not None:
                self.table[column].config(text=user_input)

        if column == 2:
            bot_name = self.table[0].cget("text")
            bot_password = self.table[1].cget("text")

            if not (bot_name and bot_password):
                self.write(
                    f"Please enter a bot name and a bot password before checking."
                )
                return

            self.write(f"Trying connexion to Metin2Wiki with the bot {bot_name}...")
            new_bot = Bot(name=bot_name, password=bot_password)
            self.wiki_app.metin2wiki.change_bot(new_bot=new_bot)
            try:
                self.wiki_app.metin2wiki.login()
            except ConnectionError as err:
                self.write(err)
            else:
                self.write(f"Sucess! The bot {bot_name} is now saved.")
                self.bot_management.save_new_bot(new_bot=new_bot)

    def write(self, text):
        self.console_frame.write(text)
