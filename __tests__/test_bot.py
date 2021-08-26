import unittest
from bot.classes.prediction import Prediction
from bot.classes.bet import Bet
from bot import Bot

# TESTING
class TestPrediction(unittest.TestCase):

    def test_sum(self):
        self.assertEqual(sum([1, 2, 3]), 6, "Should be 6")
    
if __name__ == '__main__':
    unittest.main()

class TestBet(unittest.TestCase):
    def test_sum(self):
        self.assertEqual(sum([1, 2, 3]), 6, "Should be 6")
        
if __name__ == '__main__':
    unittest.main()