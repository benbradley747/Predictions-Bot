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
            total_points += bet.amt
            if bet.prediction == result:
                self.winners.append(bet)
                total_won += bet.amt
        
        ratio = total_points / total_won

        self.resolved = True

    def add_bet(self, bet):
        self.bets.append(bet)
        self.users.append(bet.user)

    def check_valid_bet(self, user):
        if user in self.users:
            return False
        return True
    
    def build_bets_list(self):
        bets_list = ""
        for bet in self.bets:
            predicted = "yes" if bet.prediction else "no"
            bets_list += str(bet.user.name) + ": " + predicted + ", " + str(bet.amt) + "\n"
        return bets_list

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

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("token.txt", "r") as f:
    lines = f.readlines()
    token = lines[0].strip()

bot = commands.Bot(command_prefix="$")
prediction = Prediction("", None)

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

    em = discord.Embed(title = f"{user.name}'s balance")
    em.add_field(name = "Wallet", value = wallet_amt)
    await ctx.send(embed = em)

@bot.command()
async def predict(ctx, prompt):
    user = ctx.author
    prediction.prompt = prompt
    prediction.creator = user

    em = discord.Embed(title = f"{prediction.creator.name}'s prediction")
    em.add_field(name = str(prediction.prompt), value = "No current bets")
    await ctx.send(embed = em)

@bot.command()
async def bet(ctx, result, amt):
    user = ctx.author
    bet = Bet(amt, result, user)

    if await check_valid_wallet(user, amt):
        if prediction.check_valid_bet(user):
            prediction.add_bet(bet)

            bets_list = prediction.build_bets_list()
            await subtract(user, amt)

            em = discord.Embed(title = f"{prediction.creator.name}'s bet")
            em.add_field(name = str(prediction.prompt), value = bets_list)
            await ctx.send(f"{user.name} bet " + str(amt))
            await ctx.send(embed = em)
        else:
            await ctx.send("You cannot bet twice")
    else:
        await ctx.send("Insufficent funds")

# Helper methods
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

bot.run(token)
