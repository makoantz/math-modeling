import unittest
from src.model.bar_model import BarModel

class TestBarModel(unittest.TestCase):

    def test_bar_representation(self):
        # Given a set of variables
        variables = {
            'mango': 165,
            'papaya': 165 + 120,
            'grapefruit': (165 + 120) - 45
        }
        
        # When creating a BarModel
        model = BarModel(variables)
        
        # Then the bar representation should match expected values
        expected_representation = {
            'mango': 165,
            'papaya': 285,
            'grapefruit': 240
        }
        
        self.assertEqual(model.get_representation(), expected_representation)

if __name__ == '__main__':
    unittest.main()