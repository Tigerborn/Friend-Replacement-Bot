#Main bot file
import discord
from typing import Literal
import Gamblers_Den as Gambling
from discord import app_commands
import os
import logging
from dotenv import load_dotenv
from discord.ext import commands
import Weather_Satellite as Weather
import asyncio
import aiohttp
import Database_Helpers as db
import Game_Tracking as gt
import datetime

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OwnerID = int(os.getenv("OWNER_ID"))

class MyBot(commands.Bot):
    #Creating setup hook
    async def setup_hook(self):
        await db.init_db_pool()
        for gid in (1025497829646549092, 1086077024373850243):
            await self.tree.sync(guild=discord.Object(id=gid))
        await self.tree.sync()
        # Optionally warm up shared clients here:
        self.aiohttp_session = aiohttp.ClientSession()
        self.weather_client = Weather.WeatherClient(self.aiohttp_session)
        self.fortnite_client = gt.Fortnite_Client(self.aiohttp_session)

        asyncio.create_task(gt.shop_refresh(datetime.time(0,0), self.aiohttp_session))


intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.reactions = True
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
bot = MyBot(command_prefix= "/", intents = intents)

#Weather client

_original_close = bot.close
async def _close():
    if getattr(bot, "aiohttp_session", None) and not bot.aiohttp_session.closed:
        await bot.aiohttp_session.close()
    await _original_close()
    await db.close_db_pool()
bot.close = _close

@bot.event
async def on_ready():
    print("Logged in successfully as", bot.user.name, "🤯😎")
@bot.event
async def on_member_join(member: discord.Member):
    channel = member.guild.system_channel
    if channel is not None:
        await channel.send(f"Hello {member.mention}!")

async def send_chunked(interaction: discord.Interaction, content: str):
    #Sends outputs greater than 2000 character in chunks
    # Split on newlines/spaces so we don’t cut words mid-way
    chunks = []
    text = content
    LIMIT = 2000

    while text:
        if len(text) <= LIMIT:
            chunks.append(text)
            break
        # take a safe window
        window = text[:1900]
        # try to break nicely
        cut = max(window.rfind("\n"), window.rfind(" "))
        if cut < 1200:  # fallback if no good break
            cut = 1900
        chunks.append(text[:cut])
        text = text[cut:]

    if not interaction.response.is_done():
        await interaction.response.send_message(chunks[0])
        for c in chunks[1:]:
            await interaction.followup.send(c)
    else:
        for c in chunks:
            await interaction.followup.send(c)

#Cleaning up Validation with helper

def _location_params(city, zip_code, lat, lon):
    provided = 0
    if city is not None: provided += 1
    if zip_code is not None: provided += 1
    if (lat is not None) and (lon is not None): provided += 1
    if (lat is not None) ^ (lon is not None):
        return provided, "Please provide both latitude **and** longitude."
    return provided, None

#Convert True/False to Y/N

def bool_to_yn(val):
    if val is True:
        return "Y"
    if val is False:
        return "N"
    return val  # leaves strings like "Y"/"N" untouched

#SLASH: /claim_daily
@bot.tree.command(name = "claim_daily", description = "Claim your daily credits!")
async def claim_daily(interaction: discord.Interaction):
    await interaction.response.defer()
    message = await db.daily_claim(db.db_pool,interaction.user.id, interaction.user.name)
    await interaction.followup.send(message, ephemeral = True)

#SLASH: /db_view

@bot.tree.command(name="db_view", description= "Only the owner can access this")
@app_commands.default_permissions() #Makes it hidden
#Sends a view of the database to owner
async def db_view(interaction: discord.Interaction):
    if interaction.user.id != OwnerID:
        await interaction.response.send_message("You can't use this command.", ephemeral = True)
        return
    await interaction.response.defer()
    database = await db.show_databases(db.db_pool)
    table = await db.show_tables(db.db_pool)
    full = database + table
    await interaction.followup.send(full, ephemeral = True)

#SLASH: /weather

@bot.tree.command(name = "weather", description = "Dump relevant current weather info for desired location. Can give alerts if prompted")
@app_commands.describe(city = "City name (e.g., Houston)", zip = "ZIP code (e.g., 77339)", lat = "Latitude (e.g., 32.7781)",
                       lon = "Longitude (e.g., -118.7781)", alert = "Shows available alerts. Enter Y or y to enable", dump = "Give all weather info instead of relevant info. Enter Y or y to enable.")
async def weather(
        interaction: discord.Interaction,
        city: str = None,
        zip: str = None,
        lat: float = None,
        lon: float = None,
        alert: bool = False,
        dump: bool = False
):

        # --- Validation ---
        client = bot.weather_client
        dump = bool_to_yn(dump)
        alert = bool_to_yn(alert)

        count, err = _location_params(city, zip, lat, lon)
        if err:
            await interaction.response.send_message(err, ephemeral = True)
            return
        if count == 0:
            await interaction.response.send_message("Please provide **city**, **zip**, or **latitude + longitude**.", ephemeral = True)
            return
        if count > 1:
            await interaction.response.send_message(
                "Please provide only one type of location input (city, zip, or lat+lon).", ephemeral = True)
            return

        # --- Build query ---
        if city:
            query = city
        elif zip:
            query = zip
        else:
            query = f"{lat},{lon}"

        await interaction.response.defer()

        try:
            msg = await client.weather(query, alert, dump)
            await interaction.followup.send(msg)
        except asyncio.TimeoutError:
            await interaction.followup.send("Weather service timed out. Please try again.", ephemeral = True)
        except Exception as e:
            await interaction.followup.send(f"Error: `{e}`", ephemeral = True)


#SLASH: /map
@bot.tree.command(name="map", description = "Returns a desired map")
@app_commands.describe(map_type = "Type of map. Options include tmp2m (Temperature at 2m), precip (Precipitation), pressure, and wind",
                       date = "Date in format of yyyymmdd (Example: For November 1st, 2024 the input would be 20241101. Has to be within the last 3 days. Cannot be the current date or future date. EX: If today was 11/11/2025 you could only see 11/10/2025 and earlier within constraints.",
                       hour = "UTC hour in 24 format (Example: 1 PM would be 13)",
                       zoom = "Zoom level: Each Zoom corresponds to different depths of info. 0 - Whole world, 1 - Very zoomed out, 5 - Continental scale, 8 - Regional, and 10 - City-level",
                       lat = "Latitude coordinate",
                       lon = "Longitude coordinate"
                       )
async def map(
        interaction: discord.Interaction,
        map_type: str = "precip",
        date: str = Weather.map_date(Weather.get_future_date(-1)),
        hour: str = "1",
        zoom: int = 0,
        lat: float = 1.0,
        lon: float = 1.0,
):
    VALID_MAPS = {"tmp2m", "precip", "pressure", "wind"}
    if map_type not in VALID_MAPS:
        await interaction.response.send_message(f"Map type must be one of: {', '.join(sorted(VALID_MAPS))}", ephemeral = True)
        return
    try:
        hour_int = int(hour)
        if not (0 <= hour_int <= 23):
            raise ValueError
    except:
        await interaction.response.send_message("`hour` must be an integer from 0–23 (UTC).", ephemeral = True)
        return
    url = Weather.map_link(map_type, date, hour, zoom, lat, lon)
    await interaction.response.send_message(url)


#SLASH: /forecast

@bot.tree.command(name="forecast", description = "The hourly forecast for the desired day")
@app_commands.describe(city="City name (e.g., Houston)", zip="ZIP code (e.g., 77339)", lat="Latitude (e.g., 32.7781)",
                       lon="Longitude (e.g., -118.7781)", date="The day you wish to view forecast for, up to 4 days from current day. Please enter in MM/DD/YYYY format. Default is today",
                       daily = "Shows the daily forecast. On by default, type N or n to disable",
                       hourly = "Shows the hourly forecast. Type Y or y to enable. Warning: Because of large amount of content that hourly spits out, It will automatically disable daily, alert, and from_current features",
                       from_current = "Shows the forecast for each day until the day inputted. Enter Y or y to enable",
                       alert = "Shows available alerts. Enter Y or y to enable", dump = "Give all forcast info instead of relevant info. Enter Y or y to enable.")
async def forecast(interaction: discord.Interaction,
                   city: str = None,
                   zip: str = None,
                   lat: float = None,
                   lon: float = None,
                   date: str = Weather.get_date(),
                   daily: bool = True,
                   hourly: bool = False,
                   from_current: bool = False,
                   alert: bool = False,
                   dump: bool = False):

    # --- Validation ---
    client = bot.weather_client
    dump = bool_to_yn(dump)
    alert = bool_to_yn(alert)
    hourly = bool_to_yn(hourly)
    from_current = bool_to_yn(from_current)
    daily = bool_to_yn(daily)

    if hourly == "Y":
        daily = "N"
        alert = "N"
        from_current = "N"

    is_proper = Weather.date_check(date)
    if not is_proper:
        await interaction.response.send_message(
            f"Date was not in proper format (MM/DD/YYYY). Please ensure it is between {Weather.get_date()} - {Weather.get_future_date(4)}", ephemeral = True
        )
        return

    if Weather.days_between(date) > 4:
        await interaction.response.send_message(
            f"Please select a date between {Weather.get_date()} - {Weather.get_future_date(4)}", ephemeral = True
        )
        return

    count, err = _location_params(city, zip, lat, lon)
    if err:
        await interaction.response.send_message(err, ephemeral = True)
        return
    if count == 0:
        await interaction.response.send_message("Please provide **city**, **zip**, or **latitude + longitude**.", ephemeral = True)
        return
    if count > 1:
        await interaction.response.send_message(
            "Please provide only one type of location input (city, zip, or lat+lon).", ephemeral = True)
        return
    await interaction.response.defer()

    # --- Build query ---
    if city:
        query = city
    elif zip:
        query = zip
    else:
        query = f"{lat},{lon}"

    try:
        msg = await client.forecast(
            query=query,
            date=date,
            daily=daily,
            hourly=hourly,
            current_to_date=from_current,
            emergency=alert,
            dump=dump,
        )
        await send_chunked(interaction, msg)
    except asyncio.TimeoutError:
        await interaction.followup.send("Forecast request timed out.", ephemeral = True)
    except Exception as e:
        await interaction.followup.send(f"Error: `{e}`", ephemeral = True)

@bot.tree.command(name = "show_fortnite_shop", description = "Shows fortnite shop inventory")
async def show_fortnite_shop(interaction: discord.Interaction):
    client = bot.fortnite_client
    data = await client.daily_shop()
    await send_chunked(interaction, data)



bot.run(TOKEN,log_handler=handler,log_level=logging.DEBUG)