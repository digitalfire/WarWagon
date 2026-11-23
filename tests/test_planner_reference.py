import unittest
from dataclasses import asdict
from benchmarks.planner.reference import FIXTURES, STRATEGIES, run, simulate

class PlannerReferenceTests(unittest.TestCase):
    def test_all_fixture_strategies_run(self):
        for f in FIXTURES:
            for s in STRATEGIES:
                with self.subTest(fixture=f,strategy=s):
                    r = simulate(f,s,0,16)
                    self.assertLessEqual(r.actions, 16)
                    self.assertLessEqual(r.verified_count, r.actions)
                    self.assertGreaterEqual(r.verified_reward, 0)
                    self.assertEqual(r.duplicates, 0)

    def test_deterministic_replay(self):
        for f in FIXTURES:
            for s in STRATEGIES:
                self.assertEqual(asdict(simulate(f,s,7,18)), asdict(simulate(f,s,7,18)))

    def test_action_budget(self):
        for n in [1,3,9]:
            self.assertLessEqual(simulate('wide','hybrid',0,n).actions,n)

    def test_not_identical_strategies(self):
        results = run([0,1,2],12,4)
        outcomes = {(r.strategy,r.fixture,r.seed):r.trace_digest for r in results}
        self.assertTrue(any(outcomes['hierarchical',f,0] != outcomes['single',f,0] for f in FIXTURES))

    def test_invalid(self):
        with self.assertRaises(ValueError): simulate('unknown','single',0,16)
        with self.assertRaises(ValueError): simulate('wide','single',0,0)

if __name__ == '__main__':
    unittest.main()
