import discord
import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event

async def on_ready():
    print (f"Logged in as {bot.user} (ID: {bot.user.id})")
    print ("------")
    
@bot.command()

async def ping(ctx):
    await ctx.send("pong!")
    
bot.run(TOKEN)