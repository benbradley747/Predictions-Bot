class Prediction:
    def __init__(self, prompt, creator):
        self.prompt = str(prompt)
        self.creator = creator
        self.resolved = False
        self.locked = False
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
        self.locked = False
        self.bets = []
        self.users = []
        self.winners = []
        self.ratio = 0.0
        self.total_pot = 0.0