from typing import get_type_hints

import polars as pl

INT = pl.Int32
STRING = pl.String
FLOAT = pl.Float32

LANG_ENCODING = {
    "ae": "Windows-1256",
    "de": "ISO-8859-1",
    "dk": "ISO-8859-1",
    "en": "ISO-8859-1",
    "es": "ISO-8859-1",
    "fr": "Windows-1252",
    "hu": "ISO-8859-1",
    "it": "Windows-1252",
    "nl": "ISO-8859-1",
    "pl": "Windows-1252",
    "pt": "ISO-8859-1",
    "ro": "ISO-8859-16",
    "ru": "windows-1251",
    "tr": "Windows-1252",
}


class MobProtoVariables:
    VNUM: INT = "Vnum"
    RANK: STRING = "Rank"
    TYPE: STRING = "Type"
    BATTLE_TYPE: STRING = "BattleType"
    LEVEL: INT = "Level"
    AI_FLAGS_0: STRING = "AiFlags0"
    AI_FLAGS_1: STRING = "AiFlags1"
    RACE_FLAGS: STRING = "RaceFlags"
    IMMUNE_FLAGS: STRING = "ImmuneFlags"
    ST: INT = "St"
    DX: INT = "Dx"
    HT: INT = "Ht"
    IQ: INT = "Iq"
    SUNGMA_ST: INT = "SungMaSt"
    SUNGMA_DX: INT = "SungMaDx"
    SUNGMA_HT: INT = "SungMaHt"
    SUNGMA_IQ: INT = "SungMaIq"
    MIN_DAMAGE: INT = "MinDamage"
    MAX_DAMAGE: INT = "MaxDamage"
    MAX_HP: INT = "MaxHp"
    REGEN_CYCLE: INT = "RegenCycle"
    REGEN_PERCENT: INT = "RegenPercent"
    EXP: INT = "Exp"
    SUNGMA_EXP: INT = "SungMaExp"
    DEF: INT = "Def"
    ATTACK_SPEED: INT = "AttackSpeed"
    MOVE_SPEED: INT = "MoveSpeed"
    AGGRESSIVE_HP_PCT: INT = "AggressiveHpPct"
    AGGRESSIVE_SIGHT: INT = "AggressiveSight"
    ATTACK_RANGE: INT = "AttackRange"
    DROP_ITEM_GROUP: INT = "DropItemGroup"
    ENCHANT_CURSE: INT = "EnchantCurse"
    ENCHANT_SLOW: INT = "EnchantSlow"
    ENCHANT_POISON: INT = "EnchantPoison"
    ENCHANT_STUN: INT = "EnchantStun"
    ENCHANT_CRITICAL: INT = "EnchantCritical"
    ENCHANT_PENETRATE: INT = "EnchantPenetrate"
    RESIST_FIST: INT = "ResistFist"
    RESIST_SWORD: INT = "ResistSword"
    RESIST_TWO_HANDED: INT = "ResistTwoHanded"
    RESIST_DAGGER: INT = "ResistDagger"
    RESIST_BELL: INT = "ResistBell"
    RESIST_FAN: INT = "ResistFan"
    RESIST_BOW: INT = "ResistBow"
    RESIST_CLAW: INT = "ResistClaw"
    RESIST_FIRE: INT = "ResistFire"
    RESIST_ELECT: INT = "ResistElect"
    RESIST_MAGIC: INT = "ResistMagic"
    RESIST_WIND: INT = "ResistWind"
    RESIST_POISON: INT = "ResistPoison"
    RESIST_BLEEDING: INT = "ResistBleeding"
    ATT_ELEC: INT = "AttElec"
    ATT_FIRE: INT = "AttFire"
    ATT_ICE: INT = "AttIce"
    ATT_WIND: INT = "AttWind"
    ATT_EARTH: INT = "AttEarth"
    ATT_DARK: INT = "AttDark"
    RESIST_DARK: INT = "ResistDark"
    RESIST_ICE: INT = "ResistIce"
    RESIST_EARTH: INT = "ResistEarth"
    DAM_MULTIPLY: FLOAT = "DamMultiply"
    DRAIN_SP: INT = "DrainSp"

    CALCULATOR_MOB_COLS = [
        VNUM,
        RANK,
        TYPE,
        LEVEL,
        RACE_FLAGS,
        ST,
        DX,
        HT,
        IQ,
        MIN_DAMAGE,
        MAX_DAMAGE,
        DEF,
        ENCHANT_CRITICAL,
        ENCHANT_PENETRATE,
        RESIST_FIST,
        RESIST_SWORD,
        RESIST_TWO_HANDED,
        RESIST_DAGGER,
        RESIST_BELL,
        RESIST_FAN,
        RESIST_BOW,
        RESIST_CLAW,
        RESIST_FIRE,
        RESIST_ELECT,
        RESIST_MAGIC,
        RESIST_WIND,
        ATT_ELEC,
        ATT_FIRE,
        ATT_ICE,
        ATT_WIND,
        ATT_EARTH,
        ATT_DARK,
        RESIST_DARK,
        RESIST_ICE,
        RESIST_EARTH,
        DAM_MULTIPLY,
    ]

    PAGE_MOB_COLS = [
        VNUM,
        RANK,
        BATTLE_TYPE,
        LEVEL,
        AI_FLAGS_0,
        RACE_FLAGS,
        EXP,
        SUNGMA_EXP,
        DROP_ITEM_GROUP,
        ENCHANT_SLOW,
        ENCHANT_POISON,
        ENCHANT_STUN,
        ATT_ELEC,
        ATT_FIRE,
        ATT_ICE,
        ATT_WIND,
        ATT_EARTH,
        ATT_DARK,
        DRAIN_SP,
    ]

    RANK_MAPPING = {
        "PAWN": 1,
        "S_PAWN": 2,
        "KNIGHT": 3,
        "S_KNIGHT": 4,
        "BOSS": 5,
        "KING": 6,
    }

    TYPE_MAPPING = {"MONSTER": 0, "STONE": 1}

    RACE_MAPPING = {
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

    @classmethod
    def get_value_type(cls) -> dict[str, str]:
        return {
            getattr(cls, name): type_hint
            for name, type_hint in get_type_hints(cls).items()
            if type_hint is not (list, dict)
        }


class ItemProtoVariable:
    VNUM: STRING = "Vnum"
    TYPE: STRING = "Type"
    SUB_TYPE: STRING = "SubType"
    ANTI_FLAGS: STRING = "AntiFlags"
    VALUE0: INT = "Value0"
    VALUE1: INT = "Value1"
    VALUE2: INT = "Value2"
    VALUE3: INT = "Value3"
    VALUE4: INT = "Value4"
    VALUE5: INT = "Value5"

    WEAPON_MAPPING = {
        "WEAPON_SWORD": 0,
        "WEAPON_DAGGER": 1,
        "WEAPON_BOW": 2,
        "WEAPON_TWO_HANDED": 3,
        "WEAPON_BELL": 4,
        "WEAPON_CLAW": 5,
        "WEAPON_FAN": 6,
    }

    WEAPON_INFO = [
        "ITEM_WEAPON",
        "ANTI_MUSA",
        [21900, 21976],
        [7180, 7189],
    ]

    WEAPON_FIST = {0: ["Poings", 8, [0, 0, 0, 0], []]}

    @classmethod
    def get_value_type(cls) -> dict[str, str]:
        return {
            getattr(cls, name): type_hint
            for name, type_hint in get_type_hints(cls).items()
            if type_hint is not (list, dict)
        }


class ToWiki:
    AGGRESSIVE = "Aggressive"
    WIKI_NAME = "wiki_name"
    TRUE = pl.lit("O")
    FALSE = pl.lit("N")
    NONE = "Aucun"
    AGGR = "AGGR"

    TO_WIKI = {
        MobProtoVariables.VNUM: "Vnum",
        MobProtoVariables.RANK: "Rang",
        MobProtoVariables.LEVEL: "Niveau",
        MobProtoVariables.RACE_FLAGS: "Type",
        MobProtoVariables.BATTLE_TYPE: "Dégâts",
        MobProtoVariables.DROP_ITEM_GROUP: "Drop",
        AGGRESSIVE: "Agressif",
        MobProtoVariables.ENCHANT_POISON: "Poison",
        MobProtoVariables.ENCHANT_SLOW: "Ralentissement",
        MobProtoVariables.ENCHANT_STUN: "Étourdissement",
        MobProtoVariables.EXP: "Exp",
        MobProtoVariables.ATT_ELEC: "Élément",
        MobProtoVariables.DRAIN_SP: "PM",
    }

    RANK_MAPPING = {
        "PAWN": "1",
        "S_PAWN": "2",
        "KNIGHT": "3",
        "S_KNIGHT": "4",
        "BOSS": "Boss",
        "KING": "5",
    }

    BATTLE_MAPPING = {
        "MELEE": "Melee",
        "POWER": "Melee",
        "TANKER": "Melee",
        "MAGIC": "Magique",
        "RANGE": "Fleche",
    }

    RACE_MAPPING = {
        "DEVIL": "M",
        "DESERT": "D",
        "HUMAN": "Dh",
        "ANIMAL": "A",
        "UNDEAD": "Mv",
        "ORC": "O",
        "MILGYO": "My",
        "INSECT": "I",
    }

    ELEMENT_MAPPING = {
        MobProtoVariables.ATT_ELEC: "F",
        MobProtoVariables.ATT_FIRE: "Feu",
        MobProtoVariables.ATT_ICE: "G",
        MobProtoVariables.ATT_WIND: "V",
        MobProtoVariables.ATT_EARTH: "T",
        MobProtoVariables.ATT_DARK: "O",
    }

    EFFECT_NAMES = [
        MobProtoVariables.ENCHANT_SLOW,
        MobProtoVariables.ENCHANT_POISON,
        MobProtoVariables.ENCHANT_STUN,
    ]
