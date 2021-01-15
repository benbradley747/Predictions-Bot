import discord
from discord.ext import commands

import json
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("token.txt", "r") as f:
    lines = f.readlines()
    token = lines[0].strip()

bot = commands.Bot(command_prefix="$")

@bot.event
async def on_ready():
    print("Logged in as:")
    print(bot.user.name)
    print(bot.user.id)
    print("Bot is ready")

# Commands
@bot.command()
async def balance(ctx):
    user = ctx.author
    await open_account(user)
    users = await get_users()

    wallet_amt = users[str(user.id)]["wallet"]

    em = discord.Embed(title = f"{ctx.author.name}'s balance")
    em.add_field(name = "Wallet", value = wallet_amt)
    await ctx.send(embed = em)

@bot.command()
async def add(ctx, amt: int):
    if amt >= 0:
        user = ctx.author
        await open_account(user)
        users = await get_users()

        users[str(user.id)]["wallet"] += amt

        if users[str(user.id)]["wallet"] < 0:
            users[str(user.id)]["wallet"] = 0

        with open("bank.json", "w") as f:
            json.dump(users, f)
    else:
        await ctx.send("Please input a positive integer")

@bot.command()
async def subtract(ctx, amt: int):
    if amt >= 0:
        user = ctx.author
        await open_account(user)
        users = await get_users()

        users[str(user.id)]["wallet"] -= amt

        if users[str(user.id)]["wallet"] < 0:
            users[str(user.id)]["wallet"] = 0

        with open("bank.json", "w") as f:
            json.dump(users, f)
    else:
        await ctx.send("Please input a positive integer")

# Helper methods
async def open_account(user):
    users = await get_users()

    if str(user.id) in users:
        return False
    else:
        users[str(user.id)] = {}
        users[str(user.id)]["wallet"] = 0

    with open("bank.json", "w") as f:
        json.dump(users, f)
    return True

async def get_users():
    with open("bank.json", "r") as f:
        users = json.load(f)
    return users

bot.run(token)