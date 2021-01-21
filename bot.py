import discord
from discord.ext import commands
from bot.classes.bet import Bet
from bot.classes.prediction import Prediction
import json
import os
import os.path
from os import path

# Global stuff
prefix = "$"
prediction = Prediction("", None)
daily_reward: int = 500
time_intervals = (
    ('hours', 3600),
    ('minutes', 60),
    ('seconds', 1),
)

# Set up
bot = commands.Bot(command_prefix=prefix)
bot.remove_command("help")
os.chdir(os.path.dirname(os.path.abspath(__file__)))
token = os.getenv("DISCORD_BOT_TOKEN")

if path.exists("token.txt"):
    with open("token.txt", "r") as f:
        lines = f.readlines()
        token = lines[0].strip()

# Events
@bot.event
async def on_ready():
    print("Logged in as:")
    print(bot.user.name)
    print(bot.user.id)
    print("Bot is ready")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"This command is on cooldown, you can use it again in {display_time(int(error.retry_after))}")

# Commands
@bot.command()
async def balance(ctx):
    user = ctx.author
    await open_account(user)
    users = await get_users()

    wallet_amt = users[str(user.id)]["wallet"]

    em = discord.Embed(
        title = f"{user.name}'s balance"
    )

    em.add_field(name = "Wallet", value = wallet_amt)
    await ctx.send(embed = em)

@bot.command()
async def predict(ctx, *, prompt):
    if prediction.prompt == "":
        user = ctx.author
        prediction.prompt = prompt
        prediction.creator = user

        em = discord.Embed(
            title = f"{prediction.creator.name}'s prediction\n" + prediction.prompt,
            colour = discord.Colour.random()
        )

        em.set_thumbnail(url="https://cdn.discordapp.com/attachments/799651569943183360/801330005820964914/casino-gambling.jpg")
        em.add_field(name = "Status: Active", value = "No current bets")
        em.add_field(name = "Total Pot", value = "0", inline = False)

        await ctx.send(embed = em)
    else:
        await ctx.send("You cannot start a new prediction while another is active.")

@bot.command()
async def bet(ctx, amt, result):
    if prediction.prompt != "":
        if not prediction.locked:
            user = ctx.author
            if amt == "all-in":
                users = await get_users()
                amt = users[str(user.id)]["wallet"]
                await ctx.send(f"{user.name} is going all in!")
            bet = Bet(amt, result, user)

            if await check_valid_wallet(user, amt):
                if prediction.check_valid_bet(user):
                    prediction.add_bet(bet)
                    prediction.update_total_pot(bet.amt)

                    bets_list = prediction.build_bets_list(False)
                    await subtract(user, amt)
                    status_string = "Active" if prediction.resolved == False else "Completed"
                    locked_string = "Locked" if prediction.locked == True else "Unlocked"

                    em = discord.Embed(
                        title = f"{prediction.creator.name}'s prediction\n" + prediction.prompt,
                        description = "Status: " + status_string + "\nLocked: " + locked_string,
                        colour = discord.Colour.random()
                    )

                    em.set_thumbnail(url="https://cdn.discordapp.com/attachments/799651569943183360/801330005820964914/casino-gambling.jpg")
                    em.add_field(
                        name = "Yes",
                        value = "No current bets" if bets_list[0] == "" else bets_list[0]
                    )
                    em.add_field(name = "No",
                        value = "No current bets" if bets_list[1] == "" else bets_list[1]
                    )
                    em.add_field(name = "Total Pot", value = prediction.get_total_pot(), inline = False)
            
                    await ctx.send(f"{user.name} bet " + str(amt) + " on " + result)
                    await ctx.send(embed = em)
                else:
                    await ctx.send("You cannot bet twice")
            else:
                await ctx.send("Insufficent funds")
        else:
            await ctx.send("You cannot place anymore bets on a locked prediction")
    else:
        await ctx.send("There is no active prediction to bet on")

@bot.command()
async def result(ctx, conc):
    user = ctx.author
    if user.id == prediction.get_creator_id():
        users = await get_users()
        result = True if conc == "yes" else False
        prediction.resolve(result)
        if prediction.winners:
            winners_list = prediction.build_bets_list(prediction.winners, True)
            for bet in prediction.winners:
                await add_funds(bet.user, users, bet.amt)
        else:
            winners_list = "Nobody won :("

        em = discord.Embed(
            title = f"{prediction.creator.name}'s prediction\nStatus: Completed"
        )
        
        em.add_field(name = "Big Winners!", value = winners_list)

        await ctx.send(f"{user.name} resolved the bet with result: '" + str(conc) + "'")
        await ctx.send(embed = em)

        prediction.reset_prediction()
    else:
        await ctx.send("Only the creator of this prediction (" + prediction.creator.name + ") can resolve it.")

@bot.command()
async def lock(ctx):
    user = ctx.author
    if user.id == prediction.get_creator_id():
        prediction.locked = True if not prediction.locked else False
    else:
        await ctx.send("Only the creator of this prediction (" + prediction.creator.name + ") can lock it.")
    
@bot.command()
async def current(ctx):
    status_string = "Active" if prediction.resolved == False else "Completed"
    locked_string = "Locked" if prediction.locked == True else "Unlocked"
    bets_list = prediction.build_bets_list(False)

    em = discord.Embed(
        title = f"{prediction.creator.name}'s prediction\n" + prediction.prompt,
        description = "Status: " + status_string + "\nLocked: " + locked_string,
        colour = discord.Colour.random()
    )

    em.set_thumbnail(url="https://cdn.discordapp.com/attachments/799651569943183360/801330005820964914/casino-gambling.jpg")
    em.add_field(
        name = "Yes",
        value = "No current bets" if bets_list[0] == "" else bets_list[0]
    )
    em.add_field(
        name = "No",
        value = "No current bets" if bets_list[1] == "" else bets_list[1]
    )
    em.add_field(name = "Total Pot", value = prediction.get_total_pot(), inline = False)

    await ctx.send(embed = em)

@bot.command()
@commands.cooldown(1, 60*60*24, commands.cooldowns.BucketType.user)
async def daily(ctx):
    user = ctx.author
    await open_account(user)
    users = await get_users()
    await add_funds(user, users, daily_reward)
    await write_data("bot/bank.json", users)
    await ctx.send(f"{user.name} claimed their daily reward")
    await balance(ctx)

@bot.command()
async def leaderboard(ctx):
    em = discord.Embed(title = "Leaderboard")

    await ctx.send(embed = em)

@bot.command(pass_context = True)
async def help(ctx):
    em = discord.Embed(title = "Help")
    em.add_field(name = "$balance", value = "Shows your current balance", inline = False)
    em.add_field(name = "$daily", value = "Gives the author their daily reward", inline = False)
    em.add_field(name = "$predict <prompt>", value = "Creates a new prediction with the given prompt", inline = False)
    em.add_field(name = "$bet <amount> <yes/no>", value = "Creates a new yes/no bet with the given amount", inline = False)
    em.add_field(name = "$lock", value = "Locks the currently active prediction. Predicitions can only be locked by its creator")
    em.add_field(name = "$result <yes/no>", value = "Resolves your current prediction with yes/no and pays out the winning players", inline = False)

    await ctx.send(embed = em)

# Helper methods
async def add_funds(user, users, amt: int):
    users[str(user.id)]["wallet"] += amt

    await write_data("bot/bank.json", users)
    
    print("added " + str(amt) + f" to {user.name}'s wallet")

@bot.command()
async def add(ctx, amt: int):
    if amt >= 0:
        user = ctx.author
        await open_account(user)
        users = await get_users()

        users[str(user.id)]["wallet"] += amt

        await write_data("bot/bank.json", users)
    else:
        await ctx.send("Please input a positive integer")

async def subtract(user, amt):
    await open_account(user)
    users = await get_users()
    new_balance = int(users[str(user.id)]["wallet"]) - int(amt)

    users[str(user.id)]["wallet"] = new_balance
    await write_data("bot/bank.json", users)

async def check_valid_wallet(user, amt_removed):
    await open_account(user)
    users = await get_users()

    if int(amt_removed) > int(users[str(user.id)]["wallet"]):
        return False
    else:
        return True

async def open_account(user):
    users = await get_users()

    if str(user.id) in users:
        if users[str(user.id)]["name"] == "":
            users[str(user.id)]["name"] = str(user.name)
            await write_data("bot/bank.json", users)
        return False
    else:
        users[str(user.id)] = {}
        users[str(user.id)]["name"] = str(user.name)
        users[str(user.id)]["wallet"] = 100

    await write_data("bot/bank.json", users)
    return True

async def get_users():
    with open("bot/bank.json", "r") as f:
        users = json.load(f)
    return users

async def write_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def display_time(seconds, granularity=2):
    result = []

    for name, count in time_intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])

bot.run(token)
