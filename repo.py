# Repository for WoW Data Retrieval

from typing import Any


import aiohttp

import os
import time


from utils import format_slug, get_xp_progress, get_wowhead_creature_link, VERSION

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


async def get_creature_summary(
        session: aiohttp.ClientSession,
        access_token: str,
        creature_id: str,
        region = "us",
        locale = "en_US"
) -> dict:

    namespace = f"static-{VERSION}-{region}"

    url = f"https://{region}.api.blizzard.com/data/wow/creature/{creature_id}"
    params = {"namespace": namespace, "locale": locale}
    headers = {"Authorization": f"Bearer {access_token}"}

    async with session.get(url, params=params, headers=headers) as response:
        if response.status == 404:
            return {"error": f"Error: Creature {id} not found."}
        if response.status >= 400:
            return {"error": "HTTP Error fetching creature summary."}

        data = await response.json()

        c_id = data.get("id", creature_id)
        c_name = data.get("name", "Unknown")
        t_name = data.get("type", {}).get("name", "Unknown")
        family = data.get("family", {}).get("name", "Unknown")
        tameable = "Yes" if data.get("is_tameable") else "No"
        wowhead_url = get_wowhead_creature_link(creature_id)

        return {
            "id": c_id,
            "name": c_name,
            "type": t_name,
            "family": family,
            "tameable": tameable,
            "wowhead_url": wowhead_url
        }

async def search_items(
        session: aiohttp.ClientSession,
        access_token: str,
        search_query: str,
        max_results = 24,
        region = "us",
        locale = "en_US",
) -> dict:

    namespace = f"static-{VERSION}-{region}"

    url = f"https://{region}.api.blizzard.com/data/wow/search/item"
    params = {"namespace": namespace, f"name.{locale}": search_query,
              "orderby": "id", "_page": 1, "locale": locale}
    headers = {"Authorization": f"Bearer {access_token}"}

    search_terms = search_query.lower().split()
    items_found = []

    async with session.get(url, params=params, headers=headers) as response:
        if response.status == 404:
            return {"error": f"Error: Item '{search_query}' not found."}
        if response.status >= 400:
            return {"error": "HTTP Error searching items."}

        data = await response.json()

        results = data.get("results", [])

        if not results or len(results) == 0:
            return {"error": "No items found."}

        for item in results:
            current = item.get("data", {})
            id = current.get("id")
            name = current.get("name", {}).get(locale, "Unknown")

            if id and all(term in name.lower() for term in search_terms):
                items_found.append({"id": id, "name": name})
            if len(items_found) > max_results:
                break

        return {
            "query": search_query,
            "results": items_found
        }


async def search_creatures(
        session: aiohttp.ClientSession,
        access_token: str,
        query: str,
        max_results = 24,
        region = "us",
        locale = "en_US"
) -> dict:

    namespace = f"static-{VERSION}-{region}"

    url = f"https://{region}.api.blizzard.com/data/wow/search/creature"
    params = {"namespace": namespace, f"name.{locale}": query, "orderby": "id", "_page": 1, "locale": locale}
    headers = {"Authorization": f"Bearer {access_token}"}


    search_terms = query.lower().split()
    creatures_found = []

    async with session.get(url, params=params, headers=headers) as response:
        if response.status == 404:
            return {"error": f"Error: Creature '{query}' not found."}
        if response.status >= 400:
            return {"error": "HTTP Error searching creatures."}

        data = await response.json()

        results = data.get("results", [])

        if not results or len(results) == 0:
            return {"error": "No creatures found."}

        for item in results:
            current = item.get("data", {})
            id = current.get("id")
            name = current.get("name", {}).get(locale, "Unknown")

            if id and all(term in name.lower() for term in search_terms):
                creatures_found.append({"id": id, "name": name})
            if len(creatures_found) > max_results:
                break

        return {
            "query": query,
            "results": creatures_found
        }


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


async def get_character_specs(
    session: aiohttp.ClientSession,
    access_token: str,
    first_name: str,
    last_name: str,
    region = "us",
    locale = "en_US",
) -> dict:
    char_slug = format_slug(f"{first_name} {last_name}")
    full_name = f"{first_name.lower().capitalize()} {last_name.lower().capitalize()}"
    namespace = f"profile-{VERSION}-{region}"

    url = f"https://{region}.api.blizzard.com/profile/wow/character/{char_slug}/specializations"
    params = {"namespace": namespace, "locale": locale}
    headers = {"Authorization": f"Bearer {access_token}"}

    async with session.get(url, params=params, headers=headers) as response:
        if response.status == 404:
            return {"error": f"Character '{full_name}' not found."}
        if response.status >= 400:
            return {"error": f"HTTP Error fetching specializations: {response.status}"}

        data: dict = await response.json()

        spec_groups: list[dict] = data.get("specialization_groups", [])
        active_group = next((g for g in spec_groups if g.get("is_active")), None)

        if not active_group:
            return {"error": f"No active specialization found for '{full_name}'."}

        trees: list[dict] = []
        for tree in active_group.get("specializations") or []:
            tree_name: str = tree.get("specialization", {}).get("name", "Unknown Tree")
            talents_raw: list[dict] = tree.get("talents") or []

            talents: list[dict[str, str | int]] = [
                {
                    "name": t.get("talent", {}).get("name", "Unknown"),
                    "rank": t.get("talent_rank", 0),
                }
                for t in talents_raw
            ]

            trees.append({
                "tree": tree_name,
                "talents": talents,
            })

        return {
            "character": full_name,
            "version": VERSION,
            "trees": trees,
        }

async def get_character_summary(
        session: aiohttp.ClientSession,
        access_token: str,
        first_name: str,
        last_name: str,
        region = "us",
        locale = "en_US"
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