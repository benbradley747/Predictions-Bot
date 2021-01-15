import discord
from discord.ext import commands

import json
import os

if os.path.exists(os.getcwd() + 'config.json'):
    with open('./config.json') as f:
        configData = json.load(f)
else:
    configTemplate = { 'token': '', 'prefix': '$'}

    with open(os.getcwd() + '/config.json', 'w+') as f:
        json.dump(configTemplate, f)

token = configData['token']
prefix = configData['prefix']

bot = commands.Bot(command_prefix=prefix)

@bot.event
async def on_ready():
    print('Logged in as:')
    print(bot.user.name)
    print(bot.user.id)
    print('Bot is ready')

bot.run(token)
