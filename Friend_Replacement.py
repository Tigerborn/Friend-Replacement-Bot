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

@bot.tree.command(name = "weather", description = "Get weather by city, zip, or coordinates. Will give alerts if prompted")
@app_commands.describe(city = "City name (e.g., Houston)", zip = "ZIP code (e.g., 77339)", lat = "Latitude (e.g., 32.7781)",
                       lon = "Longitude (e.g., -118.7781)", alert = "Shows available alerts for the area based on any input. Leave field empty to not trigger")
async def weather(
        interaction: discord.Interaction,
        city: str = None,
        zip: str = None,
        lat: float = None,
        lon: float = None,
        alert: str = None,
):

        # --- Validation ---
        provided = [x for x in [city, zip, (lat and lon)] if x]

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

        result = Weather.get_current_weather_data(query)
        await interaction.response.send_message(result)

        #Sends alerts if the alert field is filled
        if alert is not None:
            alerts = Weather.Check_Emergency_Status(query)
            if len(alerts) >= 1:
                for alert in alerts:
                    await interaction.followup.send(alert)
            if len(alerts) == 0:
                await interaction.followup.send("There are no active alerts in your area 😱😎")






#SLASH: /weather_dump
@bot.tree.command(name = "weather_dump", description = "Get weather dump by city, zip, or coordinates. Will give alerts if prompted")
@app_commands.describe(city="City name (e.g., Houston)", zip="ZIP code (e.g., 77339)", lat="Latitude (e.g., 32.7781)",
                       lon="Longitude (e.g., -118.7781)", alert = "Shows available alerts for the area based on any input. Leave field empty to not trigger")
async def weather_dump(
        interaction: discord.Interaction,
        city: str = None,
        zip: str = None,
        lat: float = None,
        lon: float = None,
        alert: str = None
):
    # --- Validation ---
    provided = [x for x in [city, zip, (lat and lon)] if x]

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

    result = Weather.get_current_weather_data_extend(query)

    await interaction.response.send_message(result)

    # Sends alerts if the alert field is filled
    if alert is not None:
        alerts = Weather.Check_Emergency_Status(query)
        if len(alerts) >= 1:
            for alert in alerts:
                await interaction.followup.send(alert)
        if len(alerts) == 0:
            await interaction.followup.send("There are no active alerts in your area 😱😎")

#SLASH: /map
@bot.tree.command(name="map", description = "Returns a desired map")
@app_commands.describe(map_type = "Type of map. Options include tmp2m (Temperature at 2m), precip (Precipitation), pressure, and wind",
                       date = "Date in format of yyyymmdd (Example: For November 1st, 2024 the input would be 20241101. Can only be 3 days or less of the current date",
                       hour = "UTC hour in 24 format (Example: 1 PM would be 13)",
                       zoom = "Zoom level",
                       x = "X coordinate",
                       y = "Y coordinate"
                       )
async def map(
        interaction: discord.Interaction,
        map_type: str = None,
        date: str = None,
        hour: str = None,
        zoom: int = None,
        x: int = None,
        y: int = None,
):
    if map_type != "tmp2m" and map_type != "precip" and map_type != "pressure" and map_type != "wind": #If the map type is wrong tell them
        await interaction.response.send_message("Please ensure that Map Type is either of these four options (case sensitive): tmp2m, precip, pressure, or wind")
        return
    if map_type is None or date is None or hour is None or zoom is None or x is None or y is None:
        await interaction.response.send_message("One or more field was left empty💀. Please fill out all fields and try again.")
        return
    url = Weather.Display_Map(map_type, date, hour, zoom, x, y)
    await interaction.response.send_message(url)


#SLASH: /forecast

bot.run(TOKEN,log_handler=handler,log_level=logging.DEBUG)