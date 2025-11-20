#Game Tracking Functions
import os
from dotenv import load_dotenv
import aiohttp
import asyncio
import Database_Helpers as db

load_dotenv()

API_KEY = os.getenv("FORTNITE_API_KEY")
API_URL = os.getenv("FORTNITE_API_URL")

class Fortnite_Client:
    def __init__(self, session: aiohttp.ClientSession, timeout_sec: float = 8.0):
        self.session = session
        self.timeout = aiohttp.ClientTimeout(total=timeout_sec)
    async def _get(self, url: str):
        if not API_KEY:
            raise RuntimeError("API_KEY not set")

        async with self.session.get(url, timeout=self.timeout) as response:
            response.raise_for_status()
            return await response.json()

    async def daily_shop(self):
        #Will return data for the shop today.
        data = self.get(f"{API_URL}v2/shop")
        print(data)


