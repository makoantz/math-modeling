import unittest
from src.parser.question_parser import QuestionParser

class TestQuestionParser(unittest.TestCase):

    def setUp(self):
        self.parser = QuestionParser()

    def test_parse_simple_question(self):
        question = "A mango is 165 grams. A papaya is 120 grams heavier than the mango while the grapefruit is 45 grams lighter than the papaya."
        expected_output = {
            'mango': 165,
            'papaya': 285,  # 165 + 120
            'grapefruit': 240  # 285 - 45
        }
        result = self.parser.parse_question(question)
        self.assertEqual(result, expected_output)

    def test_parse_question_with_different_units(self):
        question = "A mango weighs 165 grams. A papaya is 120 grams heavier than the mango."
        expected_output = {
            'mango': 165,
            'papaya': 285  # 165 + 120
        }
        result = self.parser.parse_question(question)
        self.assertEqual(result, expected_output)

    def test_parse_invalid_question(self):
        question = "What is the weight of the fruits?"
        result = self.parser.parse_question(question)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()