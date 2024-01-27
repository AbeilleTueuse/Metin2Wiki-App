from typing import Literal
import json
import polars as pl

from config.config import *
from utils.utils import UPGRADE_PATTERN
from data.files_info import (
    MobProtoVariables as MPV,
    ItemProtoVariable as IPV,
    ToWiki as TW,
    LANG_ENCODING,
)


class GameNames:
    VNUM = "VNUM"
    LOCAL_NAME = "LOCALE_NAME"
    SEPARATOR = "\t"
    SCHEMA = {VNUM: pl.Int64, LOCAL_NAME: pl.String}

    def _read_csv(self, path: str, lang: str):
        names = (
            pl.read_csv(
                source=path.format(lang=lang),
                has_header=True,
                separator=self.SEPARATOR,
                schema=self.SCHEMA,
                encoding=LANG_ENCODING[lang],
            )
            .drop_nulls()
            .with_columns(
                pl.col(self.LOCAL_NAME)
                .str.replace_all(chr(160), " ", literal=True)
                .str.strip_chars()
            )
        )

        return names


class MobNames(GameNames):
    def __init__(self, lang: str = "fr"):
        self.lang = lang
        self.data = self._read_csv(MOB_NAMES_PATH, lang)


class ItemNames(GameNames):
    def __init__(self, lang: str = "fr"):
        self.lang = lang
        self.data = self._read_csv(ITEM_NAMES_PATH, lang)

    def prepare_for_calculator(self, vnum_col: str):
        self.data = self.data.with_columns(
            pl.col(self.LOCAL_NAME).str.replace(UPGRADE_PATTERN, "")
        ).rename({self.VNUM: vnum_col})


class GameProto:
    SEPARATOR = "\t"

    def _read_csv(self, path: str, dtypes: dict) -> pl.DataFrame:
        return pl.read_csv(
            source=path,
            has_header=True,
            separator=self.SEPARATOR,
            columns=list(dtypes.keys()),
            dtypes=dtypes,
        )


class MobProto(GameProto):
    def __init__(self):
        self.data = self._read_csv(MOB_PROTO_PATH, MPV.get_value_type())

    def get_data_for_calculator(self, pages):
        pages = pl.DataFrame(
            pages, schema={MPV.VNUM: pl.Int64, TW.WIKI_NAME: pl.String}
        ).sort(MPV.VNUM)

        data = (
            self.data[MPV.CALCULATOR_MOB_COLS]
            .filter(pl.col(MPV.VNUM).is_in(pages[MPV.VNUM]))
            .with_columns(
                pl.col(MPV.RANK).replace(MPV.RANK_MAPPING, return_dtype=pl.Int8),
                pl.col(MPV.TYPE).replace(MPV.TYPE_MAPPING, return_dtype=pl.Int8),
                pl.col(MPV.RACE_FLAGS).replace(
                    MPV.RACE_MAPPING, default=-1, return_dtype=pl.Int8
                ),
                pages[TW.WIKI_NAME],
            )
            .drop(MPV.VNUM)
        )

        return {row[-1]: list(row[:-1]) for row in data.iter_rows()}

    def get_data_for_pages(self, vnums: int | list[int], lang: str):
        mob_names = MobNames(lang=lang)

        if isinstance(vnums, int):
            vnums = [vnums]

        data = (
            self.data[MPV.PAGE_MOB_COLS]
            .filter(pl.col(MPV.VNUM).is_in(vnums))
            .with_columns(
                pl.col(MPV.RANK).replace(TW.RANK_MAPPING),
                pl.col(MPV.RACE_FLAGS).replace(TW.RACE_MAPPING),
                pl.col(MPV.BATTLE_TYPE).replace(TW.BATTLE_MAPPING),
                pl.max_horizontal(MPV.EXP, MPV.SUNGMA_EXP),
                pl.concat_list(
                    pl.when(pl.col(element) >= 1)
                    .then(pl.lit(wiki_element))
                    .otherwise(None)
                    for element, wiki_element in TW.ELEMENT_MAPPING.items()
                )
                .list.drop_nulls()
                .alias(TW.ATT),
            )
            .select(TW.TO_WIKI.keys())
            .rename(TW.TO_WIKI)
        )


class ItemProto(GameProto):
    def __init__(self):
        self.data = self._read_csv(ITEM_PROTO_PATH, IPV.get_value_type())
        self.data = self._remove_string_vnum()

    def _remove_string_vnum(self):
        return self.data.with_columns(
            pl.col(IPV.VNUM).str.to_integer(strict=False),
        ).drop_nulls()

    def get_data_for_calculator(
        self, page_vnums: list[str], item_names: ItemNames, en_names: ItemNames
    ):
        item_names.prepare_for_calculator(IPV.VNUM)
        en_names.prepare_for_calculator(IPV.VNUM)

        data = (
            self.data.filter(
                pl.col("Type") == IPV.WEAPON_INFO["ITEM_WEAPON"],
                (pl.col(IPV.VNUM) <= max(page_vnums) + 9)
                & (
                    pl.col(IPV.VNUM)
                    .is_between(*IPV.WEAPON_INFO["EXCLUDE_WEAPON_RANGE"])
                    .not_()
                )
                | (pl.col(IPV.VNUM).is_between(*IPV.WEAPON_INFO["HERO_WEAPON_RANGE"])),
            )
            .with_columns(
                pl.col("SubType").replace(
                    IPV.WEAPON_MAPPING, default=-1, return_dtype=pl.Int8
                ),
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
            .join(en_names.data, on=IPV.VNUM)
            .group_by(en_names.LOCAL_NAME)
            .agg(
                pl.col(IPV.VNUM).first(),
                pl.col("SubType").first(),
                pl.first(f"Value{index}" for index in range(1, 5)),
                pl.col("Value5"),
            )
            .filter(
                pl.col(IPV.VNUM).is_in(page_vnums)
                | pl.col(IPV.VNUM).is_between(*IPV.WEAPON_INFO["HERO_WEAPON_RANGE"]),
            )
            .sort(pl.col(IPV.VNUM))
            .with_columns(pl.concat_list(f"Value{index}" for index in range(1, 5)))
            .join(item_names.data, on=IPV.VNUM, suffix=f"_{item_names.lang}")
        )

        item_data_for_calculator = IPV.WEAPON_FIST
        item_data_for_calculator.update(
            {
                row[0]: [
                    row[-1],
                    row[2],
                    row[3],
                    row[-2],
                ]
                for row in data.iter_rows()
            }
        )

        return item_data_for_calculator