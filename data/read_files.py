from collections import UserDict
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
    SCHEMA = {VNUM: pl.Int32, LOCAL_NAME: pl.String}

    def _read_csv(self, path: str, lang: str, vnum_label: str | None = None):
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

        if vnum_label is not None:
            return names.rename({self.VNUM: vnum_label})

        return names


class MobNames(GameNames):
    def __init__(self, lang: str = "fr", vnum_label: str | None = None):
        self.lang = lang
        self.data = self._read_csv(MOB_NAMES_PATH, lang, vnum_label)


class ItemNames(GameNames):
    def __init__(self, lang: str = "fr", vnum_label: str | None = None):
        self.lang = lang
        self.data = self._read_csv(ITEM_NAMES_PATH, lang, vnum_label)

    def prepare_for_calculator(self, vnum_col: str):
        self.data = self.data.with_columns(
            pl.col(self.LOCAL_NAME).str.replace(UPGRADE_PATTERN, "")
        ).rename({self.VNUM: vnum_col})


class MobDropItem(UserDict):
    START_MOB = "mob"
    END_MOB = "}"

    def __init__(self):
        super().__init__()
        self._read_data()

    def _read_data(self):
        with open(MOB_DROP_ITEM_PATH, "r") as file:
            is_reading_drop_list = False
            current_list = []
            vnum = 0

            for line in file.readlines():
                line = line.lower().strip()

                if not line:
                    continue

                if line.startswith(self.START_MOB):
                    vnum = int(line.split()[1])
                    if vnum not in self:
                        self[vnum] = []
                    is_reading_drop_list = True
                    current_list = []

                elif is_reading_drop_list and not line.startswith(self.END_MOB):
                    current_list.append(int(line.split()[1]))

                elif line.startswith(self.END_MOB):
                    self[vnum].append(current_list)
                    is_reading_drop_list = False
                    current_list = []

    def get_translation(self, vnums: list[int], item_names: pl.DataFrame):
        translation: dict[int, list[list[str]]] = {}

        for monster_vnum in vnums:
            if monster_vnum not in self:
                continue

            translation[monster_vnum] = []

            # disgusting code
            for item_vnums in self[monster_vnum]:
                item_vnums = list(sorted(item_vnums))
                item_translation = item_names.filter(pl.col(IPV.VNUM).is_in(item_vnums))
                mapping = dict(
                    zip(
                        item_translation[IPV.VNUM],
                        item_translation[ItemNames.LOCAL_NAME],
                    )
                )

                translation[monster_vnum].append(
                    [mapping[vnum] for vnum in item_vnums if vnum in mapping]
                )

        return translation


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

    def get_data_for_pages(self, vnums: int | list[int], lang: str, to_dicts=False):
        mob_names = MobNames(lang=lang, vnum_label=MPV.VNUM).data
        item_names = ItemNames(lang=lang, vnum_label=MPV.VNUM).data

        if isinstance(vnums, int):
            vnums = [vnums]

        data = (
            self.data[MPV.PAGE_MOB_COLS]
            .filter(pl.col(MPV.VNUM).is_in(vnums))
            .select(
                pl.col(MPV.VNUM),
                pl.col(MPV.LEVEL),
                pl.col(MPV.RANK).replace(TW.RANK_MAPPING),
                pl.col(MPV.RACE_FLAGS).replace(TW.RACE_MAPPING),
                pl.col(MPV.BATTLE_TYPE).replace(TW.BATTLE_MAPPING),
                pl.col(MPV.DROP_ITEM_GROUP),
                # pl.when(pl.col(MPV.DROP_ITEM_GROUP) > 0).then(
                #     item_names.filter(
                #         pl.col(MPV.VNUM).is_in(pl.col(MPV.DROP_ITEM_GROUP))
                #     )[ItemNames.LOCAL_NAME]
                # ),
                # pl.col(MPV.DROP_ITEM_GROUP).map(
                #     lambda col: item_names.filter(pl.col(MPV.VNUM).is_in(col))[
                #         ItemNames.LOCAL_NAME
                #     ]
                # ),
                pl.max_horizontal(MPV.EXP, MPV.SUNGMA_EXP),
                pl.concat_list(
                    pl.when(pl.col(element) >= 1)
                    .then(pl.lit(wiki_element))
                    .otherwise(None)
                    for element, wiki_element in TW.ELEMENT_MAPPING.items()
                )
                .list.drop_nulls()
                .keep_name(),
                pl.when(pl.col(MPV.AI_FLAGS_0).str.split(",").list.contains(TW.AGGR))
                .then(TW.TRUE)
                .otherwise(TW.FALSE)
                .alias(TW.AGGRESSIVE),
                *[
                    pl.when(pl.col(col_name) > 0)
                    .then(TW.TRUE)
                    .otherwise(TW.FALSE)
                    .keep_name()
                    for col_name in TW.EFFECT_NAMES
                ],
                pl.col(MPV.DRAIN_SP),
            )
            .with_columns(
                pl.when(pl.col(MPV.ATT_ELEC).list.len() == 0)
                .then([TW.NONE])
                .otherwise(pl.col(MPV.ATT_ELEC))
                .keep_name()
            )
            .join(mob_names, on=MPV.VNUM)
            .rename(TW.TO_WIKI)
        )

        mob_drops = MobDropItem().get_translation(vnums, item_names)

        if to_dicts:
            return data.to_dicts(), mob_drops

        return data, mob_drops


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
        (
            item_weapon_label,
            anti_musa_label,
            hero_weapon_range,
            exclude_weapon_range,
        ) = IPV.WEAPON_INFO

        data = (
            self.data.filter(
                pl.col(IPV.TYPE) == item_weapon_label,
                (pl.col(IPV.VNUM) <= max(page_vnums) + 9)
                & (pl.col(IPV.VNUM).is_between(*exclude_weapon_range).not_())
                | (pl.col(IPV.VNUM).is_between(*hero_weapon_range)),
            )
            .with_columns(
                pl.col(IPV.SUB_TYPE).replace(
                    IPV.WEAPON_MAPPING, default=-1, return_dtype=pl.Int8
                ),
            )
            .with_columns(
                pl.when(
                    pl.col(IPV.SUB_TYPE) == 0,
                    pl.col(IPV.ANTI_FLAGS).str.contains(anti_musa_label),
                )
                .then(7)
                .otherwise(pl.col(IPV.SUB_TYPE))
                .keep_name()
            )
            .join(en_names.data, on=IPV.VNUM)
            .group_by(en_names.LOCAL_NAME)
            .agg(
                pl.col(IPV.VNUM).first(),
                pl.col(IPV.SUB_TYPE).first(),
                pl.first(f"Value{index}" for index in range(1, 5)),
                pl.col(IPV.VALUE5),
            )
            .filter(
                pl.col(IPV.VNUM).is_in(page_vnums)
                | pl.col(IPV.VNUM).is_between(*hero_weapon_range),
            )
            .sort(pl.col(IPV.VNUM))
            .with_columns(pl.concat_list(f"Value{index}" for index in range(1, 5)))
            .join(item_names.data, on=IPV.VNUM)
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
