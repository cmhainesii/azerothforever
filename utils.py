"""
***----------------------------------------------------------------------------
*** HELPER / UTILITY FUNCTIONS
***>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""


import urllib.parse
import math
from config import VERSION, MAX_LEVEL

FOREVER_XP_TABLE = {
    1: 400, 2: 900, 3: 1400, 4: 2100, 5: 2800, 6: 3600, 7: 4500, 8: 5400, 9: 6500, 10: 7600,
    11: 8800, 12: 10100, 13: 11400, 14: 12900, 15: 14400, 16: 16000, 17: 17700, 18: 19400, 19: 21300, 20: 23200,
    21: 25200, 22: 27300, 23: 29400, 24: 31700, 25: 34000, 26: 36400, 27: 38900, 28: 41400, 29: 44300, 30: 47400,
    31: 50800, 32: 54500, 33: 58600, 34: 62800, 35: 67100, 36: 71600, 37: 76100, 38: 80800, 39: 85700, 40: 90700,
    41: 95800, 42: 101000, 43: 106300, 44: 111800, 45: 117500, 46: 123200, 47: 129100, 48: 135100, 49: 141200, 50: 147500,
    51: 153900, 52: 160400, 53: 167100, 54: 173900, 55: 180800, 56: 187900, 57: 195000, 58: 202300, 59: 209800
}




WOW_CLASS_COLORS: dict[str, int] = {
    "Warrior": 0xC69B6D,
    "Paladin": 0xF48CBA,
    "Hunter": 0xAAD372,
    "Rogue": 0xFFF468,
    "Priest": 0xFFFFFF,
    "Death Knight": 0xC41E3A,
    "Shaman": 0x0070DD,
    "Mage": 0x3FC7EB,
    "Warlock": 0x8788EE,
    "Monk": 0x00FF98,
    "Druid": 0xFF7C0A,
    "Demon Hunter": 0xA330C9,
    "Evoker": 0x33937F,
}

WOWHEAD_BASE_URL = "https://wowhead.com"



def to_wowhead_version(version: str) -> str:
    if version == "tbc":
        return "tbc"
    elif version == "era":
        return "classic"
    elif version == "mop":
        return "mop-classic"
    elif version == "forever":
        return "forever"
    else:
        return "invalid"

def get_wowhead_item_link(id: str) -> str:
    return f"{WOWHEAD_BASE_URL}/{VERSION}/item={id}"


def get_wowhead_creature_link(id: str) -> str:
    return f"{WOWHEAD_BASE_URL}/{VERSION}/npc={id}/"


def is_valid_version(version: str) -> bool:
    VALID_VERSIONS = { "era", "tbc", "mop", "forever" }

    return version in VALID_VERSIONS

def format_with_gold(copper_in) -> str :
    gold = copper_in // 10_000
    silver = copper_in % 10_000 // 100
    copper = copper_in % 100
    return f"{gold}g {silver}s {copper}c"

def format_slug(name: str) -> str:
    cleaned = name.strip().lower().replace(' ', '-').replace("'", "")
    # Percent-encode Unicode characters (e.g. 'ö' becomes '%C3%B6')
    return urllib.parse.quote(cleaned)

def get_xp_progress(level: int, current_xp: int) -> str:

    if level >= MAX_LEVEL:
        return "Max Level"

    needed_xp = FOREVER_XP_TABLE.get(level)

    if not needed_xp:
        return "Unknown"

    pct = math.ceil((current_xp / needed_xp) * 100)
    return f"{pct:.1f}"