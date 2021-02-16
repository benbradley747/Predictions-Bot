class Prediction:
    def __init__(self, prompt, creator):

        """ str : The prompt for this prediction """
        self.prompt = str(prompt)

        """ User : User object for the creator of this prediction """
        self.creator = creator

        """ bool : Determines whether this prediction is resolved or not """
        self.resolved = False

        """ bool : Determines whether this prediction is locked or not """
        self.locked = False

        """ Bets[] : List of the current bets on this prediction """
        self.bets = []

        """ str : Used to display the current bits in the prediction embed """
        self.bets_list = ""

        """ User[] : List of users currently betting on this prediction """
        self.users = []

        """ User[] : List of users that won this prediction """
        self.winners = []

        """ float : total prize pot / total amount won """
        self.ratio = 0.0

        """ float : Total prize pot"""
        self.total_pot = 0.0
    
    def resolve(self, result: bool):
        """
        Resolves the predicion.
            - Builds the list of winners based on the result
            - Finds the ratio used to calculate the winnings later

        Parameters
        ----------
        result : bool
            The result the prediction should resolve to.
        """

        total_won = 0.0
        for bet in self.bets:
            if bet.prediction == result:
                self.winners.append(bet)
                total_won += bet.get_amt()

        self.ratio = self.total_pot / (total_won if self.winners else 1.0)
        self.resolved = True

    def add_bet(self, bet):
        """
        Adds a bet to the prediction.

        Parameters
        ----------
        bet : Bet
            Bet object to add to the prediction.
        """

        self.bets.append(bet)
        self.users.append(bet.user)

    def check_valid_bet(self, user):
        """
        Checks whether or not a bet is valid. A bet is invalid if the use who created
        it has made a bet on this prediction already

        Parameters
        ----------
        user : User
            User object to look for in users.
        """

        if user in self.users:
            return False
        return True
    
    def build_bets_list(self, bets, winners: bool):
        """
        Builds a str to represent the current bets on this prediction and returns it.
            - Sorts the list of bets by their amounts.
            - Parses the list of bets into a str that will get displayed later in an embed.
            - Calculates winnings for each bet (if prediction is being resolved).
        
        Parameters
        ----------
        winners : bool
            Determines whether to build a regular bets list or a list of winners if the
            prediction is being resolved.
        """

        # Array with a length of 3, stores yes string, no string, and winners string.
        # Used when resolving or betting on a prediction. Provides a string to display in the embed
        #
        # bets_list[0] = string of users that bet on yes ('User: 100\n', if they bet on yes)
        # bets_list[1] = string of users that bet on no ('User: 100\n', if they bet on no)
        # bets_list[2] = string of users that won this prediction ('1. User won 1000!\n')
        bets_lists = [ "", "", "" ]

        self.bets.sort(key = lambda x: x.amt, reverse = True)
        count = 0

        if not self.winners:
            bets_lists[2] = "Nobody won :("

        for bet in bets:
            if winners:
                count += 1
                winnings = bet.get_amt() * self.ratio
                bet.amt = int(winnings)
                bets_lists[2] += str(count) + ". " + str(bet.user.name) + " won " + str(bet.get_amt()) + "!\n"
            else:
                bet_string = str(bet.user.name) + ": " + str(bet.amt) + "\n"
                if bet.prediction == True:
                    bets_lists[0] += bet_string
                else:
                    bets_lists[1] += bet_string
        return bets_lists

    def reset_prediction(self):
        """ Resets this prediction, must be called before creating a new prediction. """
        self.prompt = ""
        self.creator = None
        self.resolved = False
        self.locked = False
        self.bets = []
        self.users = []
        self.winners = []
        self.ratio = 0.0
        self.total_pot = 0.0

    def abandon_bet(self, abandoner):
        """ Removes a bet from the list of bets on this prediction """
        self.bets = [bet for bet in self.bets if bet.user != abandoner]

    # Getters/Setters/Updaters
    def update_total_pot(self, amt):
        self.total_pot += amt

    def get_total_pot(self):
        return int(self.total_pot)
    
    def get_creator_id(self):
            return self.creator.id