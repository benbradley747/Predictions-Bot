import discord
from bot.classes import Bet

class Prediction:
    def __init__(self, prompt):
        self.prompt = prompt
        self.resolved = False
        self.bets = []
        self.winners = []

    def resolve(self, result):
        total_points = 0
        total_won = 0
        for bet in bets:
            total_points += bet.amt
            if bet.prediction == result:
                self.winners.append(bet)
                total_won += bet.amt
        
        ratio = total_points / total_won

        self.resolved = True

    def add_bet(self, bet):
        self.bets.append(bet)
    


    
