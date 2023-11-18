# %%
import pandas as pd
from typing import Literal


PATHS = {
    "mob_proto": r"data\mob_proto.txt",
    "mob_proto_old": r"data\mob_proto_old.txt",
    "mob_template": r"data\mob_template.txt",
    "item_proto": r"data\item_proto.txt",
    "result": {
        "weapons": r"data\result\weapon_data.txt",
        "monsters": r"data\result\monster_data.txt",
    },
    "fr": {
        "item_names": r"data\fr\item_names.txt",
        "mob_names": r"data\fr\mob_names.txt",
    },
    "en": {
        "item_names": r"data\en\item_names.txt",
        "mob_names": r"data\en\mob_names.txt",
    },
}


class MobProto:
    MAPPING = {
        "rank": {
            "PAWN": "1",
            "S_PAWN": "2",
            "KNIGHT": "3",
            "S_KNIGHT": "4",
            "BOSS": "Boss",
            "KING": "5",
        },
        "battle": {
            "MELEE": "Melee",
            "POWER": "Melee",
            "TANKER": "Melee",
            "MAGIC": "Magique",
            "RANGE": "Fleche",
        },
        "race": {
            "DEVIL": "M",
            "DESERT": "D",
            "HUMAN": "Dh",
            "ANIMAL": "A",
            "UNDEAD": "Mv",
            "ORC": "O",
            "MILGYO": "My",
            "INSECT": "I",
        },
        "element": {
            "AttElec": "F",
            "AttFire": "Feu",
            "AttIce": "G",
            "AttWind": "V",
            "AttEarth": "T",
            "AttDark": "O",
        },
        "columns": {
            "Level": "Niveau",
            "Rank": "Rang",
            "RaceFlags": "Type",
            "Element": "Élément",
            "BattleType": "Dégâts",
            "DrainSp": "PM",
            "AGGR": "Agressif",
            "EnchantSlow": "Ralentissement",
            "EnchantStun": "Étourdissement",
            "EnchantPoison": "Poison",
        },
    }

    NO_VALUE = "Aucun"
    TRUE_VALUE = "O"
    FALSE_VALUE = "N"

    def __init__(self, processing: Literal["default", "wiki_data"], get_template=False):
        self.processing = processing
        self.data = self._read_csv()
        if get_template:
            self.template = self._get_template()

    def _get_template(self):
        with open(file=PATHS["mob_template"], mode="r", encoding="utf-8") as file:
            return file.read()

    def _read_csv(self):
        mob_names = pd.read_csv(
            PATHS["fr"]["mob_names"],
            index_col="VNUM",
            encoding="Windows-1252",
            sep="\t",
        )

        # usecols = [
        #     'Vnum', 'Rank', 'Type', 'BattleType',
        #     'Level', 'AiFlags0', 'RaceFlags', 'Exp', 'SungMaExp',
        #     'EnchantSlow', 'EnchantPoison', 'EnchantStun',
        #     'AttElec', 'AttFire', 'AttIce', 'AttWind',
        #     'AttEarth', 'AttDark', 'DrainSp'
        # ]

        data = pd.read_csv(
            PATHS["mob_proto"],
            index_col="Vnum",
            # usecols = usecols,
            encoding="ISO-8859-1",
            sep="\t",
        )

        if self.processing == "default":
            data = self._data_processing(data)
        elif self.processing == "wiki_data":
            pass

        data["NameFR"] = mob_names.loc[data.index]
        data["NameFR"] = data["NameFR"].str.replace(chr(160), " ")

        return data

    def _get_old_data(self):
        old_data = pd.read_csv(
            PATHS["mob_proto_old"],
            index_col="VNUM",
            # usecols = usecols,
            encoding="ISO-8859-1",
            sep="\t",
        )

        return old_data

    def _filter_rows(self, data: pd.DataFrame):
        data = data[data["Type"] == "MONSTER"]
        data = data.drop("Type", axis=1)

        return data

    def _replace_values(self, data: pd.DataFrame):
        data["Rank"].replace(self.MAPPING["rank"], inplace=True)
        data["BattleType"].replace(self.MAPPING["battle"], inplace=True)
        data["RaceFlags"].replace(self.MAPPING["race"], inplace=True)
        data["RaceFlags"].fillna(self.NO_VALUE, inplace=True)

        return data

    def _element_processing(self, data: pd.DataFrame):
        element_mapping: dict = self.MAPPING["element"]
        element_names = element_mapping.values()

        def process(row: pd.Series):
            row = row[element_names]
            elements = "|".join(row[row != 0].index.to_list())
            return elements if elements else self.NO_VALUE

        data.rename(columns=element_mapping, inplace=True)
        data["Element"] = data.apply(process, axis=1)
        data = data.drop(element_names, axis=1)

        return data

    def _handle_exp(self, data: pd.DataFrame):
        data["Exp"] = data.apply(lambda row: max(row["Exp"], row["SungMaExp"]), axis=1)
        data = data.drop("SungMaExp", axis=1)

        return data

    def _handle_flags(self, data: pd.DataFrame):
        data["AiFlags0"].fillna("", inplace=True)
        data["AGGR"] = (
            data["AiFlags0"]
            .str.contains("AGGR")
            .apply(lambda x: self.TRUE_VALUE if x else self.FALSE_VALUE)
        )

        data = data.drop("AiFlags0", axis=1)

        return data

    def _handle_effects(self, data: pd.DataFrame):
        for column in ["EnchantSlow", "EnchantStun", "EnchantPoison"]:
            data[column] = data[column].apply(
                lambda x: self.TRUE_VALUE if x else self.FALSE_VALUE
            )

        return data

    def _change_columns_type(self, data: pd.DataFrame):
        for column in data.columns:
            data[column] = data[column].astype(str)

        return data

    def _rename_columns(self, data: pd.DataFrame):
        return data.rename(columns=self.MAPPING["columns"])

    def _data_processing(self, data: pd.DataFrame):
        data = self._filter_rows(data)
        data = self._replace_values(data)
        data = self._element_processing(data)
        data = self._handle_exp(data)
        data = self._handle_flags(data)
        data = self._handle_effects(data)
        data = self._change_columns_type(data)
        data = self._rename_columns(data)

        return data

    def dam_multiply_correction(self, data: pd.DataFrame):
        true_dam_multiply = self._get_old_data()["DAM_MULTIPLY"]

        for vnum in true_dam_multiply.index:
            if vnum in data.index:
                dam_multiply_new = data.loc[vnum, "DamMultiply"]
                dam_multiply_old = true_dam_multiply.loc[vnum]

                if dam_multiply_old != dam_multiply_new:
                    print(vnum, dam_multiply_new, dam_multiply_old)

        # data.loc[data.index.isin(true_dam_multiply.index), 'DamMultiply'] = true_dam_multiply

        return data

    def create_wiki_monster_data(self, vnums: tuple, titles: tuple):
        usecols = [
            "Rank",
            "Type",
            "Level",
            "RaceFlags",
            "St",
            "Dx",
            "Ht",
            "Iq",
            "MinDamage",
            "MaxDamage",
            "Def",
            "EnchantCritical",
            "EnchantPenetrate",
            "ResistFist",
            "ResistSword",
            "ResistTwoHanded",
            "ResistDagger",
            "ResistBell",
            "ResistFan",
            "ResistBow",
            "ResistClaw",
            "ResistFire",
            "ResistElect",
            "ResistMagic",
            "ResistWind",
            "AttElec",
            "AttFire",
            "AttIce",
            "AttWind",
            "AttEarth",
            "AttDark",
            "ResistDark",
            "ResistIce",
            "ResistEarth",
            "DamMultiply",
            "NameFR",
        ]

        rank_mapping = {
            "PAWN": 1,
            "S_PAWN": 2,
            "KNIGHT": 3,
            "S_KNIGHT": 4,
            "BOSS": 5,
            "KING": 6,
        }

        type_mapping = {"MONSTER": 0, "STONE": 1}

        race_mapping = {
            "ANIMAL": 0,
            "HUMAN": 1,
            "ORC": 2,
            "MILGYO": 3,
            "UNDEAD": 4,
            "INSECT": 5,
            "DESERT": 6,
            "DEVIL": 7,
            "OUTPOST": -1,
        }

        data: pd.DataFrame = self.data.loc[vnums, usecols]
        data["Rank"].replace(rank_mapping, inplace=True)
        data["Type"].replace(type_mapping, inplace=True)
        data["RaceFlags"].replace(race_mapping, inplace=True)
        data["RaceFlags"].fillna(-1, inplace=True)
        data["RaceFlags"] = data["RaceFlags"].astype(int)
        data["NameFR"] = titles

        data = self.dam_multiply_correction(data)

        data = data.to_numpy().tolist()

        monster_data_wiki = {
            monster_data[-1]: monster_data[:-1] for monster_data in data
        }

        with open(PATHS["result"]["monsters"], "w") as file:
            print(monster_data_wiki, file=file)


class ItemProto:
    MAX_VNUM_WEAPON = 7509
    WEAPON_MAPPING = {
        "WEAPON_SWORD": 0,
        "WEAPON_DAGGER": 1,
        "WEAPON_BOW": 2,
        "WEAPON_TWO_HANDED": 3,
        "WEAPON_BELL": 4,
        "WEAPON_CLAW": 5,
        "WEAPON_FAN": 6,
    }
    WEAPON_TO_REMOVE = [
        210,
        220,
        230,
        260,
        1140,
        1150,
        1160,
        2190,
        3170,
        3180,
        3200,
        4030,
        5130,
        5140,
        5150,
        7170,
        7180,
    ]

    def __init__(self, processing: Literal["default", "weapon"] = "default"):
        self.processing = processing
        self.data = self._read_csv()

    def _read_csv(self):
        data = pd.read_csv(PATHS["item_proto"], encoding="ISO-8859-1", sep="\t")

        data = data[pd.to_numeric(data["Vnum"], errors="coerce").notnull()]
        data.set_index("Vnum", inplace=True)
        data.index = data.index.astype(int)

        data = self._add_translation(data)

        if self.processing == "default":
            data = self._default_processing(data)

        elif self.processing == "weapon":
            data = self._add_translation(data, lang="en")
            data = self._weapon_processing(data)

        return data

    def _add_translation(self, data: pd.DataFrame, lang="fr"):
        item_names = pd.read_csv(
            PATHS[lang]["item_names"],
            index_col="VNUM",
            encoding="Windows-1252",
            sep="\t",
        )

        column_name = f"Name{lang.upper()}"

        data[column_name] = item_names.loc[data.index]
        data[column_name] = data[column_name].str.replace(chr(160), " ")

        return data

    def _default_processing(self, data: pd.DataFrame):
        equipments = (
            (data["Type"] == "ITEM_WEAPON")
            | (data["Type"] == "ITEM_ARMOR")
            | (data["Type"] == "ITEM_BELT")
        )

        data.loc[equipments, "NameFR"] = data.loc[equipments, "NameFR"].str.replace(
            r" ?\+\d+", "", regex=True
        )
        data.loc[equipments, "NameFR"] = data.loc[equipments, "NameFR"].drop_duplicates(
            keep="first"
        )
        data.dropna(inplace=True)

        return data

    def _weapon_processing(self, data: pd.DataFrame):
        data = pd.concat([data.loc[: self.MAX_VNUM_WEAPON], data.loc[21900:21976]])

        data = data[data["SubType"].isin(self.WEAPON_MAPPING.keys())]

        data.drop(
            [
                index
                for start_index in self.WEAPON_TO_REMOVE
                for index in range(start_index, start_index + 10)
            ],
            inplace=True,
        )

        data.reset_index(drop=True, inplace=True)

        data["NameFR"] = data.loc[data.index, "NameFR"].str.replace(
            r"\s?\+\d+", "", regex=True
        )
        data["NameEN"] = data.loc[data.index, "NameEN"].str.replace(
            r"\s?\+\d+", "", regex=True
        )

        data["SubType"].replace(self.WEAPON_MAPPING, inplace=True)

        return data

    def create_weapon_data(self, weapon):
        weapon_dataframe = self.data[self.data["NameEN"] == weapon]

        weapon_base = weapon_dataframe.iloc[0]

        weapon_base_values = weapon_base[[f"Value{i}" for i in range(1, 5)]].to_list()
        weapon_up = weapon_dataframe["Value5"].to_list()

        weapon_type = weapon_base["SubType"]

        if (weapon_type == 0) and ("ANTI_MUSA" in weapon_base["AntiFlags"]):
            weapon_type == 7

        return [weapon_base["NameFR"], weapon_type, weapon_base_values, weapon_up]

    def create_wiki_weapon_data(self):
        if self.processing != "weapon":
            print("Weapon processing should be used.")
            return

        weapon_data = {"Fist": ["Poings", 8, [0, 0, 0, 0], []]}
        weapon_data.update(
            {
                weapon: self.create_weapon_data(weapon)
                for weapon in self.data["NameEN"].unique()
            }
        )

        with open(PATHS["result"]["weapons"], "w") as file:
            print(weapon_data, file=file)


if __name__ == "__main__":
    # mob_proto = ItemProto(processing = 'weapon')

    # mob_proto.create_wiki_weapon_data()

    mob_proto = MobProto(processing="wiki_data")
    mob_proto.create_wiki_monster_data(
        vnums=[3960, 3961, 3962], titles=["Chien1", "Chien2", "Chien3"]
    )
