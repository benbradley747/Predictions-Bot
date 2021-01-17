import discord
from discord.ext import commands
import json
import os

class Prediction:
    def __init__(self, prompt, creator):
        self.prompt = str(prompt)
        self.creator = creator
        self.resolved = False
        self.bets = []
        self.users = []
        self.winners = []

    def resolve(self, result):
        total_points = 0
        total_won = 0
        for bet in self.bets:
            total_points += int(bet.amt)
            if bet.prediction == result:
                self.winners.append(bet)
                total_won += int(bet.amt)
        
        ratio = total_points / total_won

        self.resolved = True

    def add_bet(self, bet):
        self.bets.append(bet)
        self.users.append(bet.user)

    def check_valid_bet(self, user):
        if user in self.users:
            return False
        return True
    
    def build_bets_list(self, bets):
        bets_list = ""
        for bet in bets:
            predicted = "yes" if bet.prediction else "no"
            bets_list += str(bet.user.name) + ": " + predicted + ", " + str(bet.amt) + "\n"
        return bets_list
    
    def reset_prediction(self):
        self.prompt = ""
        self.creator = None
        self.resolved = False
        self.bets = []
        self.users = []
        self.winners = []

class Bet:
    def __init__(self, amt, predicted, user):
        self.amt = amt
        if str(predicted) == "yes":
            self.prediction = True
        elif str(predicted) == "no":
            self.prediction = False
        else:
            self.prediction = True
        self.user = user

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

os.chdir(os.path.dirname(os.path.abspath(__file__)))

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

    em = discord.Embed(title = f"{user.name}'s balance")
    em.add_field(name = "Wallet", value = wallet_amt)
    await ctx.send(embed = em)

@bot.command()
async def predict(ctx, prompt):
    user = ctx.author
    prediction.prompt = prompt
    prediction.creator = user

    em = discord.Embed(title = f"{prediction.creator.name}'s prediction\nStatus: Active")
    em.add_field(name = str(prediction.prompt), value = "No current bets")

    await ctx.send(embed = em)

@bot.command()
async def bet(ctx, result, amt):
    user = ctx.author
    bet = Bet(amt, result, user)

    if await check_valid_wallet(user, amt):
        if prediction.check_valid_bet(user):
            prediction.add_bet(bet)

            bets_list = prediction.build_bets_list(prediction.bets)
            await subtract(user, amt)
            result_string = "Active" if prediction.resolved == False else "Completed"

            em = discord.Embed(title = f"{prediction.creator.name}'s prediction\nStatus: " + result_string)
            em.add_field(name = str(prediction.prompt), value = bets_list)
            
            await ctx.send(f"{user.name} bet " + str(amt))
            await ctx.send(embed = em)
        else:
            await ctx.send("You cannot bet twice")
    else:
        await ctx.send("Insufficent funds")

@bot.command()
async def result(ctx, conc):
    user = ctx.author
    result = True if conc == "yes" else False
    result_string = "Active" if prediction.resolved == False else "Completed"
    prediction.resolve(result)
    winners_list = prediction.build_bets_list(prediction.winners)

    em = discord.Embed(title = f"{prediction.creator.name}'s prediction\nStatus: " + result_string)
    em.add_field(name = "Winners", value = winners_list)

    await ctx.send(f"{user.name} resolved the bet with result: '" + str(conc) + "'")
    await ctx.send(embed = em)

    prediction.reset_prediction()

@bot.command()
@commands.cooldown(1, 60*60*24, commands.cooldowns.BucketType.user)
async def daily(ctx):
    user = ctx.author
    await open_account(user)
    users = await get_users()

    users[str(user.id)]["wallet"] += daily_reward

    with open("bank.json", "w") as f:
        json.dump(users, f)

# Helper methods
async def add(ctx, amt: int):
    if amt >= 0:
        user = ctx.author
        await open_account(user)
        users = await get_users()

        users[str(user.id)]["wallet"] += amt

        with open("bank.json", "w") as f:
            json.dump(users, f)
    else:
        await ctx.send("Please input a positive integer")

async def subtract(user, amt):
    await open_account(user)
    users = await get_users()
    new_balance = int(users[str(user.id)]["wallet"]) - int(amt)

    users[str(user.id)]["wallet"] = new_balance
    with open("bank.json", "w") as f:
        json.dump(users, f)

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
