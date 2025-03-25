import unittest
from src.solver.equation_solver import EquationSolver

class TestEquationSolver(unittest.TestCase):

    def setUp(self):
        self.solver = EquationSolver()

    def test_solve_example_problem(self):
        # Example problem: "A mango is 165 grams. A papaya is 120 grams heavier than the mango while the grapefruit is 45 grams lighter than the papaya."
        variables = {
            'mango': 165,
            'papaya': 165 + 120,
            'grapefruit': (165 + 120) - 45
        }
        results = self.solver.solve(variables)
        self.assertEqual(results['papaya'], 285)
        self.assertEqual(results['grapefruit'], 240)

if __name__ == '__main__':
    unittest.main()