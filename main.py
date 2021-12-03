import nextcord
import asyncio
from nextcord.ext import commands
import re
from nextcord import File
from dictionaries import *
import os

token = os.environ["token"]
bot = commands.Bot(command_prefix="!", description="deez")


@bot.event
async def on_ready():
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")

    await bot.change_presence(
        status=nextcord.Status.idle,
        activity=nextcord.Activity(
            name="amiibots", type=nextcord.ActivityType.listening
        ),
    )


@bot.command(name="end")
async def end(ctx):
    exit()


for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")
        print("loaded cog")
    else:
        if os.path.isfile(filename):
            print(f"Unable to load {filename[:-3]}")

loop = asyncio.get_event_loop()
loop.run_until_complete(bot.start(token))
