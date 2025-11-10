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
    try:
        #Testing the sync
        guild = discord.Object(id=guild_id)
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


        if alert is not None:
            alerts = Weather.Check_Emergency_Status(query)
            if alerts.len() >= 1:
                for alert in alerts:
                    interaction.followup.send(alert)
            if alerts.len() == 0:
                interaction.followup.send("There are no active alerts in your area 😱😎")






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

    if alert is not None:
        alerts = Weather.Check_Emergency_Status(query)
        if alerts.len() >= 1:
            for alert in alerts:
                interaction.followup.send(alert)
        if alerts.len() == 0:
            interaction.followup.send("There are no active alerts in your area 😱😎")



bot.run(TOKEN,log_handler=handler,log_level=logging.DEBUG)