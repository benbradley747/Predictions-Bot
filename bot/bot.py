import discord
from discord.ext import commands
import json
import os

# Classes
class Prediction:
    def __init__(self, prompt, creator):
        self.prompt = str(prompt)
        self.creator = creator
        self.resolved = False
        self.bets = []
        self.users = []
        self.winners = []
        self.ratio = 0.0
        self.total_pot = 0.0

    def resolve(self, result: bool):
        total_won = 0.0
        for bet in self.bets:
            if bet.prediction == result:
                self.winners.append(bet)
                total_won += bet.get_amt()

        self.ratio = self.total_pot / (total_won if self.winners else 1.0)
        self.resolved = True

    def add_bet(self, bet):
        self.bets.append(bet)
        self.users.append(bet.user)

    def check_valid_bet(self, user):
        if user in self.users:
            return False
        return True
    
    def build_bets_list(self, bets, winners: bool):
        bets_list = ""
        if len(bets) == 0:
            return "No current bets"

        bets.sort(key = lambda x: x.amt, reverse = True)
        count = 0
        for bet in bets:
            count += 1
            if winners:
                winnings = bet.get_amt() * self.ratio
                bet.amt = int(winnings)
                bets_list += str(count) + ". " + str(bet.user.name) + " won " + str(bet.get_amt()) + "!\n"
            else:
                predicted = "yes" if bet.prediction else "no"
                bets_list += str(bet.user.name) + ": " + predicted + ", " + str(bet.amt) + "\n"
        
        return bets_list
    
    def update_total_pot(self, amt):
        self.total_pot += amt

    def get_total_pot(self):
        return int(self.total_pot)
    
    def get_creator_id(self):
            return self.creator.id
    
    def reset_prediction(self):
        self.prompt = ""
        self.creator = None
        self.resolved = False
        self.active = False
        self.bets = []
        self.users = []
        self.winners = []
        self.ratio = 0.0
        self.total_pot = 0.0

class Bet:
    def __init__(self, amt, predicted, user):
        self.amt = int(amt)
        if str(predicted) == "yes":
            self.prediction = True
        elif str(predicted) == "no":
            self.prediction = False
        else:
            self.prediction = True
        self.user = user

    def get_amt(self):
        return int(self.amt)

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
async def predict(ctx, *, prompt):
    if prediction.prompt == "":
        user = ctx.author
        prediction.prompt = prompt
        prediction.creator = user

        em = discord.Embed(title = f"{prediction.creator.name}'s prediction\nStatus: Active")
        em.add_field(name = str(prediction.prompt), value = "No current bets")
        em.add_field(name = "Total Pot", value = str(prediction.get_total_pot()), inline = False)

        await ctx.send(embed = em)
    else:
        await ctx.send("You cannot start a new prediction while another is active.")

@bot.command()
async def bet(ctx, amt, result):
    if prediction.prompt != "":
        user = ctx.author
        bet = Bet(amt, result, user)

        if await check_valid_wallet(user, amt):
            if prediction.check_valid_bet(user):
                prediction.add_bet(bet)
                prediction.update_total_pot(bet.amt)

                bets_list = prediction.build_bets_list(prediction.bets, False)
                await subtract(user, amt)
                result_string = "Active" if prediction.resolved == False else "Completed"

                em = discord.Embed(title = f"{prediction.creator.name}'s prediction\nStatus: " + result_string)
                em.add_field(name = str(prediction.prompt), value = bets_list)
                em.add_field(name = "Total Pot", value = str(prediction.get_total_pot()), inline = False)
            
                await ctx.send(f"{user.name} bet " + str(amt) + " on " + result)
                await ctx.send(embed = em)
            else:
                await ctx.send("You cannot bet twice")
        else:
            await ctx.send("Insufficent funds")
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

        em = discord.Embed(title = f"{prediction.creator.name}'s prediction\nStatus: Completed")
        em.add_field(name = "Big Winners!", value = winners_list)

        await ctx.send(f"{user.name} resolved the bet with result: '" + str(conc) + "'")
        await ctx.send(embed = em)

        prediction.reset_prediction()
    else:
        await ctx.send("Only the creator of this prediction (" + prediction.creator.name + ") can resolve it.")

@bot.command()
@commands.cooldown(1, 60*60*24, commands.cooldowns.BucketType.user)
async def daily(ctx):
    user = ctx.author
    await open_account(user)
    users = await get_users()

    users[str(user.id)]["wallet"] += daily_reward

    with open("bank.json", "w") as f:
        json.dump(users, f)
    
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
    em.add_field(name = "$bet <yes/no> <amount>", value = "Creates a new yes/no bet with the given amount", inline = False)
    em.add_field(name = "$result <yes/no>", value = "Resolves your current prediction with yes/no and pays out the winning players", inline = False)

    await ctx.send(embed = em)

# Helper methods
async def add_funds(user, users, amt: int):
    users[str(user.id)]["wallet"] += amt

    with open("bank.json", "w") as f:
        json.dump(users, f)
    
    print("added " + str(amt) + f" to {user.name}'s wallet")

@bot.command()
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
        users[str(user.id)]["name"] = str(user.name)
        users[str(user.id)]["wallet"] = 100

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
