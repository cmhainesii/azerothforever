# Repository for WoW Data Retrieval

from typing import Any

import aiohttp

import os
import time


from utils import format_slug, get_xp_progress, VERSION

from dotenv import load_dotenv

load_dotenv()


CLIENT_ID= os.getenv("BLIZZARD_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("BLIZZARD_CLIENT_SECRET", "")

async def get_valid_blizzard_token(session: aiohttp.ClientSession, token_cache: dict) -> str:
    now = time.time()

    cached_token = token_cache["access_token"]
    expires_at = token_cache["expires_at"]
    if isinstance(cached_token, str) and cached_token and isinstance(expires_at, float) and now < expires_at:
        return cached_token

    url = "https://oauth.battle.net/token"
    #auth = aiohttp.BasicAuth(CLIENT_ID, CLIENT_SECRET)
    headers = {"Authorization": aiohttp.encode_basic_auth(CLIENT_ID, CLIENT_SECRET)}

    async with session.post(url, data={"grant_type": "client_credentials"}, headers=headers) as resp:
        resp.raise_for_status()
        res = await resp.json()

        token: str = res["access_token"]
        expires_in: int = res.get("expires_in", 86400)

        token_cache["access_token"] = token
        token_cache["expires_at"] = now + expires_in - 300

        print("Fetched fresh Blizzard API token.")

        return token



async def get_character_equipment(
        session: aiohttp.ClientSession,
        access_token: str,
        first_name: str,
        last_name: str,
        region = "us",
        locale = "en_US"
) -> dict:

    char_slug = format_slug(f"{first_name} {last_name}")
    namespace = f"profile-{VERSION}-{region}"

    url = f"https://{region}.api.blizzard.com/profile/wow/character/{char_slug}/equipment"
    params = {"namespace": namespace, "locale": locale}
    headers = {"Authorization": f"Bearer {access_token}"}

    async with session.get(url, params=params, headers=headers) as response:
        if response.status == 404:
            return {"error": f"Character '{first_name.lower().capitalize()} {last_name.lower().capitalize()}' not found."}
        if response.status >= 400:
            return {"error": f"HTTP Error fetching character: {response.status}"}

        data = await response.json()
        equip_data: list[dict] = data.get("equipped_items", [])
        if not equip_data:
            return {"error": "No equipment data found."}

        equipment = [
            {
                "slot": piece.get("slot", {}).get("name", "Slot"),
                "name": piece.get("name", "Unknown Item")
            }
            for piece in equip_data
        ]

        return {
            "character": f"{first_name.lower().capitalize()} {last_name.lower().capitalize()}",
            "version": VERSION,
            "equipment": equipment
        }

async def get_character_summary(
        session: aiohttp.ClientSession,
        access_token: str,
        first_name: str,
        last_name: str,
        region: str = "us",
        locale: str = "en_US"
) -> dict:

    char_name = format_slug(f"{first_name} {last_name}")
    namespace = f"profile-{VERSION}-{region}"

    url = f"https://{region}.api.blizzard.com/profile/wow/character/{char_name}"
    params = {"namespace": namespace, "locale": locale}
    headers = {"Authorization": f"Bearer {access_token}"}

    async with session.get(url, params=params, headers=headers) as response:
        if response.status == 404:
            return {"error": f"Character '{first_name.lower().capitalize()} {last_name.lower().capitalize()}' not found."}
        if response.status >= 400:
            return {"error": f"HTTP Error fetching character: {response.status}"}

        data: dict = await response.json()

        

        # Grab the necessary data
        name = data.get("name", first_name)
        surname = data.get("surname", last_name)
        level = data.get("level", 0)
        race = data.get("race", {}).get("name", "Unknown Race")
        cls = data.get("character_class", {}).get("name", "Unknown Class")
        ruleset = data.get("ruleset", {}).get("name", "Unknown Ruleset")
        faction = data.get("faction", {}).get("name", "Unknown Faction")
        ilvl = data.get("equipped_item_level", 0)
        gender = data.get("gender", {}).get("name", "Unknown Gender")
        xp_progress_pct = get_xp_progress(level, data.get("experience", 0))

        # Guild is omitted from JSON if player is unguilded
        guild_info = ""
        if "guild" in data:
            guild_name = data["guild"].get("name")
            if guild_name:
                guild_info = f" | Guild: <{guild_name}>"

        return {
                "first_name": name.capitalize(),
                "last_name": surname.capitalize(),
                "level": level,
                "race": race,
                "class": cls,
                "faction": faction,
                "ilvl": ilvl,
                "gender": gender,
                "guild": guild_info,
                "version": "forever",
                "xp_progress_pct": xp_progress_pct,
                "ruleset": ruleset
            }