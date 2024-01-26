from typing import Literal
import json
import polars as pl

from config.config import *
from data.proto_info import (
    MOB_TYPE,
    RANK_MAPPING,
    RACE_MAPPING,
    MONSTER_TYPE_MAPPING,
    USECOLS_CALCULATOR_MOB,
    ITEM_TYPE,
    WEAPON_MAPPING,
    MAX_VNUM_WEAPON,
    HERO_WEAPON_RANGE,
    ITEM_WEAPON,
)


class GameNames:
    VNUM = "VNUM"
    LOCAL_NAME = "LOCALE_NAME"
    SEPARATOR = "\t"
    SCHEMA = {VNUM: pl.Int64, LOCAL_NAME: pl.String}

    def __init__(self, lang: str = "fr"):
        self.lang = lang
        self.encoding = self._get_encoding()
        self.mob = self._read_csv(MOB_NAMES_PATH)
        self.item = self._read_csv(ITEM_NAMES_PATH)

    def _get_encoding(self) -> dict[str, str]:
        with open(LANG_ENCODING_PATH, "r") as file:
            return json.load(file)[self.lang]

    def _read_csv(self, path: str):
        names = (
            pl.read_csv(
                source=path.format(lang=self.lang),
                has_header=True,
                separator=self.SEPARATOR,
                schema=self.SCHEMA,
                encoding=self.encoding,
            )
            .drop_nulls()
            .with_columns(
                pl.col(self.LOCAL_NAME)
                .str.replace_all(chr(160), " ", literal=True)
                .str.strip_chars()
            )
        )

        return names


class GameProto:
    VNUM = "Vnum"
    SEPARATOR = "\t"

    def __init__(self):
        self.mob = self._read_csv(MOB_PROTO_PATH, MOB_TYPE)
        self.item = self._read_csv(ITEM_PROTO_PATH, ITEM_TYPE)

    def _read_csv(self, path: str, dtypes: dict) -> pl.DataFrame:
        return pl.read_csv(
            source=path,
            has_header=True,
            separator=self.SEPARATOR,
            columns=list(dtypes.keys()),
            dtypes=dtypes,
        )

    def save_mob_data_for_calculator(self, pages):
        pages = pl.DataFrame(
            pages, schema={self.VNUM: pl.Int64, "wiki_name": pl.String}
        ).sort(self.VNUM)

        data = (
            self.mob[USECOLS_CALCULATOR_MOB]
            .filter(pl.col(self.VNUM).is_in(pages[self.VNUM]))
            .with_columns(
                pl.col("Rank").replace(RANK_MAPPING, return_dtype=pl.Int8),
                pl.col("Type").replace(MONSTER_TYPE_MAPPING, return_dtype=pl.Int8),
                pl.col("RaceFlags").replace(
                    RACE_MAPPING, default=-1, return_dtype=pl.Int8
                ),
                pages["wiki_name"],
            )
            .drop(self.VNUM)
            .to_numpy()
            .tolist()
        )

        mob_data_for_calculator = {
            monster_data[-1]: monster_data[:-1] for monster_data in data
        }

        with open(CALCULATOR_DATA_PATH, "w") as file:
            print(f"var monsterData = {mob_data_for_calculator}", file=file)
            print(f"Data saved to {CALCULATOR_DATA_PATH}.")

    def test(self, page_vnums, game_name: GameNames):
        print(game_name.item.columns, game_name.VNUM, self.VNUM, self.item.columns)
        data = (
            self.item.filter(
                pl.col("Type") == ITEM_WEAPON,
            )
            .filter(
                pl.col(self.VNUM).cast(pl.Int64).is_in(page_vnums)
                | pl.col(self.VNUM).is_between(*HERO_WEAPON_RANGE)
            )
            .with_columns(
                pl.col(self.VNUM).cast(pl.Int64),
                pl.col("SubType").replace(WEAPON_MAPPING, return_dtype=pl.Int8),
            )
            .with_columns(
                pl.when(
                    pl.col("SubType") == 0,
                    pl.col("AntiFlags").str.contains("ANTI_MUSA"),
                )
                .then(7)
                .otherwise(pl.col("SubType"))
                .alias("SubType"),
            )
            .join(game_name.item.rename({game_name.VNUM: self.VNUM}), on=self.VNUM)
            .drop(self.VNUM, "Type", "AntiFlags")
        )
        print(data)


# class MobProto:
#     MAPPING = {
#         "rank": {
#             "PAWN": "1",
#             "S_PAWN": "2",
#             "KNIGHT": "3",
#             "S_KNIGHT": "4",
#             "BOSS": "Boss",
#             "KING": "5",
#         },
#         "battle": {
#             "MELEE": "Melee",
#             "POWER": "Melee",
#             "TANKER": "Melee",
#             "MAGIC": "Magique",
#             "RANGE": "Fleche",
#         },
#         "race": {
#             "DEVIL": "M",
#             "DESERT": "D",
#             "HUMAN": "Dh",
#             "ANIMAL": "A",
#             "UNDEAD": "Mv",
#             "ORC": "O",
#             "MILGYO": "My",
#             "INSECT": "I",
#         },
#         "element": {
#             "AttElec": "F",
#             "AttFire": "Feu",
#             "AttIce": "G",
#             "AttWind": "V",
#             "AttEarth": "T",
#             "AttDark": "O",
#         },
#         "columns": {
#             "Level": "Niveau",
#             "Rank": "Rang",
#             "RaceFlags": "Type",
#             "Element": "Élément",
#             "BattleType": "Dégâts",
#             "DrainSp": "PM",
#             "AGGR": "Agressif",
#             "EnchantSlow": "Ralentissement",
#             "EnchantStun": "Étourdissement",
#             "EnchantPoison": "Poison",
#         },
#     }

#     NO_VALUE = "Aucun"
#     TRUE_VALUE = "O"
#     FALSE_VALUE = "N"

#     def __init__(self):
#         self.data = self._read_csv()

#     def _read_csv(self):
#         data = pl.read_csv(
#             MOB_PROTO_PATH,
#             index_col="Vnum",
#             encoding="ISO-8859-1",
#             sep="\t",
#         )

#         return data

#     def _get_old_data(self):
#         old_data = pd.read_csv(
#             MOB_PROTO_OLD_PATH,
#             index_col="VNUM",
#             encoding="ISO-8859-1",
#             sep="\t",
#         )

#         return old_data

#     def _filter_rows(self, data: pd.DataFrame):
#         data = data[data["Type"] == "MONSTER"]
#         data = data.drop("Type", axis=1)

#         return data

#     def _replace_values(self, data: pd.DataFrame):
#         data["Rank"].replace(self.MAPPING["rank"], inplace=True)
#         data["BattleType"].replace(self.MAPPING["battle"], inplace=True)
#         data["RaceFlags"].replace(self.MAPPING["race"], inplace=True)
#         data["RaceFlags"].fillna(self.NO_VALUE, inplace=True)

#         return data

#     def _element_processing(self, data: pd.DataFrame):
#         element_mapping: dict = self.MAPPING["element"]
#         element_names = element_mapping.values()

#         def process(row: pd.Series):
#             row = row[element_names]
#             elements = "|".join(row[row != 0].index.to_list())
#             return elements if elements else self.NO_VALUE

#         data.rename(columns=element_mapping, inplace=True)
#         data["Element"] = data.apply(process, axis=1)
#         data = data.drop(element_names, axis=1)

#         return data

#     def _handle_exp(self, data: pd.DataFrame):
#         data["Exp"] = data.apply(lambda row: max(row["Exp"], row["SungMaExp"]), axis=1)
#         data = data.drop("SungMaExp", axis=1)

#         return data

#     def _handle_flags(self, data: pd.DataFrame):
#         data["AiFlags0"].fillna("", inplace=True)
#         data["AGGR"] = (
#             data["AiFlags0"]
#             .str.contains("AGGR")
#             .apply(lambda x: self.TRUE_VALUE if x else self.FALSE_VALUE)
#         )

#         data = data.drop("AiFlags0", axis=1)

#         return data

#     def _handle_effects(self, data: pd.DataFrame):
#         for column in ["EnchantSlow", "EnchantStun", "EnchantPoison"]:
#             data[column] = data[column].apply(
#                 lambda x: self.TRUE_VALUE if x else self.FALSE_VALUE
#             )

#         return data

#     def _change_columns_type(self, data: pd.DataFrame):
#         for column in data.columns:
#             data[column] = data[column].astype(str)

#         return data

#     def _rename_columns(self, data: pd.DataFrame):
#         return data.rename(columns=self.MAPPING["columns"])

#     def _data_processing(self, data: pd.DataFrame):
#         data = self._filter_rows(data)
#         data = self._replace_values(data)
#         data = self._element_processing(data)
#         data = self._handle_exp(data)
#         data = self._handle_flags(data)
#         data = self._handle_effects(data)
#         data = self._change_columns_type(data)
#         data = self._rename_columns(data)

#         return data

#     def dam_multiply_correction(self, data: pd.DataFrame):
#         true_dam_multiply = self._get_old_data()["DAM_MULTIPLY"]

#         for vnum in true_dam_multiply.index:
#             if vnum in data.index:
#                 dam_multiply_new = data.loc[vnum, "DamMultiply"]
#                 dam_multiply_old = true_dam_multiply.loc[vnum]

#                 if dam_multiply_old != dam_multiply_new:
#                     print(vnum, dam_multiply_new, dam_multiply_old)

#         # data.loc[data.index.isin(true_dam_multiply.index), 'DamMultiply'] = true_dam_multiply

#         return data


# class ItemProto:
#     MAX_VNUM_WEAPON = 7509
#     WEAPON_TO_REMOVE = [
#         210,
#         220,
#         230,
#         260,
#         1140,
#         1150,
#         1160,
#         2190,
#         3170,
#         3180,
#         3200,
#         4030,
#         5130,
#         5140,
#         5150,
#         7170,
#         7180,
#     ]

#     def __init__(self, processing: Literal["default", "weapon"] = "default"):
#         self.processing = processing

#     def _default_processing(self, data: pd.DataFrame):
#         equipments = (
#             (data["Type"] == "ITEM_WEAPON")
#             | (data["Type"] == "ITEM_ARMOR")
#             | (data["Type"] == "ITEM_BELT")
#         )

#         data.loc[equipments, "NameFR"] = data.loc[equipments, "NameFR"].str.replace(
#             r" ?\+\d+", "", regex=True
#         )
#         data.loc[equipments, "NameFR"] = data.loc[equipments, "NameFR"].drop_duplicates(
#             keep="first"
#         )
#         data.dropna(inplace=True)

#         return data

#     # def _weapon_processing(self, data: pd.DataFrame):
#     #     data = pd.concat([data.loc[: self.MAX_VNUM_WEAPON], data.loc[21900:21976]])

#     #     data = data[data["SubType"].isin(self.WEAPON_MAPPING.keys())]

#     #     data.drop(
#     #         [
#     #             index
#     #             for start_index in self.WEAPON_TO_REMOVE
#     #             for index in range(start_index, start_index + 10)
#     #         ],
#     #         inplace=True,
#     #     )

#     #     data.reset_index(drop=True, inplace=True)

#     #     data["NameFR"] = data.loc[data.index, "NameFR"].str.replace(
#     #         r"\s?\+\d+", "", regex=True
#     #     )
#     #     data["NameEN"] = data.loc[data.index, "NameEN"].str.replace(
#     #         r"\s?\+\d+", "", regex=True
#     #     )

#     #     data["SubType"].replace(self.WEAPON_MAPPING, inplace=True)

#     #     return data

#     def create_weapon_data(self, weapon):
#         weapon_dataframe = self.data[self.data["NameEN"] == weapon]

#         weapon_base = weapon_dataframe.iloc[0]

#         weapon_base_values = weapon_base[[f"Value{i}" for i in range(1, 5)]].to_list()
#         weapon_up = weapon_dataframe["Value5"].to_list()

#         weapon_type = weapon_base["SubType"]

#         if (weapon_type == 0) and ("ANTI_MUSA" in weapon_base["AntiFlags"]):
#             weapon_type == 7

#         return [weapon_base["NameFR"], weapon_type, weapon_base_values, weapon_up]

#     def create_wiki_weapon_data(self):
#         if self.processing != "weapon":
#             print("Weapon processing should be used.")
#             return

#         weapon_data = {"Fist": ["Poings", 8, [0, 0, 0, 0], []]}
#         weapon_data.update(
#             {
#                 weapon: self.create_weapon_data(weapon)
#                 for weapon in self.data["NameEN"].unique()
#             }
#         )
