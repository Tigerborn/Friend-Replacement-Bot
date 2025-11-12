import discord
from discord import app_commands
import os
import logging
from dotenv import load_dotenv
from discord.ext import commands
import Weather_Functions as Weather

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.reactions = True
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
bot = commands.Bot(command_prefix='/', intents=intents)
@bot.event
async def on_ready():
    guild_id = 1025497829646549092
    guild_id_two = 1086077024373850243
    try:
        #Testing the sync
        guild = discord.Object(id=guild_id)
        guild_two = discord.Object(id=guild_id_two)
        await bot.tree.sync()
        print("Logged in successfully as", bot.user.name, "🤯😎")
    except Exception as e:
        print(e)

@bot.event
async def on_member_join(member: discord.Member):
    channel = member.guild.system_channel
    if channel is not None:
        await channel.send(f"Hello {member.mention}!")


#SLASH: /weather

@bot.tree.command(name = "weather", description = "Dump relevant current weather info for desired location. Can give alerts if prompted")
@app_commands.describe(city = "City name (e.g., Houston)", zip = "ZIP code (e.g., 77339)", lat = "Latitude (e.g., 32.7781)",
                       lon = "Longitude (e.g., -118.7781)", alert = "Shows available alerts. Enter Y to enable", dump = "Give all weather info instead of relevant info. Enter Y to enable.")
async def weather(
        interaction: discord.Interaction,
        city: str = None,
        zip: str = None,
        lat: float = None,
        lon: float = None,
        alert: str = "N",
        dump: str = "N"
):

        # --- Validation ---
        provided = [x for x in [city, zip, (lat and lon)] if x]
        dump = Weather.string_condenser(dump)
        alert = Weather.string_condenser(alert)

        if len(provided) == 0:
            await interaction.response.send_message("Please provide **city**, **zip**, or **latitude + longitude**.")
            return
        if len(provided) > 1:
            await interaction.response.send_message("Please provide only one type of location input (city, zip, or lat+lon).")
            return

        # --- Build query ---
        if city:
            query = city
        elif zip:
            query = zip
        else:
            query = f"{lat},{lon}"
        Weather.weather(query, alert, dump)


#SLASH: /map
@bot.tree.command(name="map", description = "Returns a desired map")
@app_commands.describe(map_type = "Type of map. Options include tmp2m (Temperature at 2m), precip (Precipitation), pressure, and wind",
                       date = "Date in format of yyyymmdd (Example: For November 1st, 2024 the input would be 20241101. Has to be within the last 3 days. Cannot be the current date or future date. EX: If today was 11/11/2025 you could only see 11/10/2025 and earlier within constraints.",
                       hour = "UTC hour in 24 format (Example: 1 PM would be 13)",
                       zoom = "Zoom level: Each Zoom corresponds to different depths of info. 0 - Whole world, 1 - Very zoomed out, 5 - Continental scale, 8 - Regional, and 10 - City-level",
                       lat = "Latitude coordinate",
                       long = "Longitude coordinate"
                       )
async def map(
        interaction: discord.Interaction,
        map_type: str = None,
        date: str = None,
        hour: str = None,
        zoom: int = None,
        lat: float = None,
        long: float = None,
):
    if map_type != "tmp2m" and map_type != "precip" and map_type != "pressure" and map_type != "wind": #If the map type is wrong tell them
        await interaction.response.send_message("Please ensure that Map Type is either of these four options (case sensitive): tmp2m, precip, pressure, or wind")
        return
    if map_type is None or date is None or hour is None or zoom is None or lat is None or long is None:
        await interaction.response.send_message("One or more field was left empty💀. Please fill out all fields and try again.")
        return
    url = Weather.map_link(map_type, date, hour, zoom, lat, long)
    await interaction.response.send_message(url)


#SLASH: /forecast

@bot.tree.command(name="forecast", description = "The hourly forecast for the desired day")
@app_commands.describe(city="City name (e.g., Houston)", zip="ZIP code (e.g., 77339)", lat="Latitude (e.g., 32.7781)",
                       lon="Longitude (e.g., -118.7781)", date="The day you wish to view forecast for, up to 4 days from current day. Please enter in MM/DD/YYYY format. Default is today",
                       daily = "Shows the daily forecast. Type Y to enable", hourly = "Shows the hourly forecast. Type Y to enable.",from_current = "Shows the forecast for each day until the day inputted. Enter Y to enable",
                       alert = "Shows available alerts for the area based on any input. Leave field empty to not trigger", dump = "Give all forcast info instead of relevant info. Enter Y to enable.")
async def forecast(interaction: discord.Interaction,
                   city: str = None,
                   zip: str = None,
                   lat: float = None,
                   lon: float = None,
                   date: str = Weather.get_date(),
                   daily: str = "N",
                   hourly: str = "N",
                   from_current: str = "N",
                   alert: str = "N",
                   dump: str = "N"):

    # --- Validation ---
    provided = [x for x in [city, zip, (lat and lon)] if x]
    dump = Weather.string_condenser(dump)
    alert = Weather.string_condenser(alert)
    hourly = Weather.string_condenser(hourly)
    from_current = Weather.string_condenser(from_current)
    if Weather.days_between(date) > 5:
        await interaction.response.send_message(f"Please select a date between {Weather.get_date()} - {Weather.get_future_date(4)}")
        return

    if len(provided) == 0:
        await interaction.response.send_message("Please provide **city**, **zip**, or **latitude + longitude**.")
        return
    if len(provided) > 1:
        await interaction.response.send_message(
            "Please provide only one type of location input (city, zip, or lat+lon).")
        return

    # --- Build query ---
    if city:
        query = city
    elif zip:
        query = zip
    else:
        query = f"{lat},{lon}"

    message = Weather.forecast(query, date, daily, hourly, from_current, alert, dump)
    interaction.response.send_message(message)


bot.run(TOKEN,log_handler=handler,log_level=logging.DEBUG)