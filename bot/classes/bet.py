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
    
    def get_predicted(self):
        return "yes" if self.prediction else "no"
