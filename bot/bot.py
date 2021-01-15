import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='$')
token = '' #this is gonna be in config.py

@bot.event
async def on_ready():
    print('Logged in as:')
    print(bot.user.name)
    print(bot.user.id)
    print('Bot is ready')

bot.run(token)
