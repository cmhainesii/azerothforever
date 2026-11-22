from discord.ext import commands
import aiohttp

import time
import os

from dotenv import load_dotenv
load_dotenv()

# Grab client secret and ID to retrieve a Blizzard API token.
CLIENT_ID= os.getenv("BLIZZARD_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("BLIZZARD_CLIENT_SECRET", "")

class AzerothBoth(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.session: aiohttp.ClientSession | None = None
        self._token_cache: dict[str, str | float] = {
            "access_token": "",
            "expires_at": 0.0 }
        
        

    async def setup_hook(self) -> None:
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()
        await super().close()

    async def get_valid_blizzard_token(self) -> str:
        now = time.time()

        cached_token = self._token_cache["access_token"]
        expires_at = self._token_cache["expires_at"]
        if isinstance(cached_token, str) and cached_token and isinstance(expires_at, float) and now < expires_at:
            return cached_token

        url = "https://oauth.battle.net/token"
        #auth = aiohttp.BasicAuth(CLIENT_ID, CLIENT_SECRET)
        headers = {"Authorization": aiohttp.encode_basic_auth(CLIENT_ID, CLIENT_SECRET)}
        assert self.session is not None
        async with self.session.post(url, data={"grant_type": "client_credentials"}, headers=headers) as resp:
            resp.raise_for_status()
            res = await resp.json()

            token: str = res["access_token"]
            expires_in: int = res.get("expires_in", 86400)

            self._token_cache["access_token"] = token
            self._token_cache["expires_at"] = now + expires_in - 300

            print("Fetched fresh Blizzard API token.")

            return token