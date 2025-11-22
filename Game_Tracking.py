#Game Tracking Functions
import os
from dotenv import load_dotenv
import aiohttp
import datetime
import asyncio
import Database_Helpers as db

load_dotenv()

API_KEY = os.getenv("FORTNITE_API_KEY")
API_URL = os.getenv("FORTNITE_API_URL")


async def shop_refresh(target: datetime.time, session: aiohttp.ClientSession):
    #Every day that the bot is active, the fortnite cache will load with the newest refresh details
    while True:
        now = datetime.datetime.now(datetime.timezone.utc)
        target_dt = datetime.datetime.combine(now.date(), target.replace(tzinfo = datetime.timezone.utc))

        if now > target_dt:
            target_dt += datetime.timedelta(days=1)

        delay = (target_dt - now).total_seconds()
        await asyncio.sleep(delay)

        async with session.get(f"{API_URL}v2/shop") as response:
            data = await response.json()
            await db.fortnite_daily_shop_cache(db.db_pool, data)




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
        data = await db.fortnite_daily_shop_pull(db.db_pool)
        if data is None:
            #If it errors out, the data will be sourced from api call
            data = await self._get(f"{API_URL}v2/shop")


        return data


