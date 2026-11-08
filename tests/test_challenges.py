import unittest
from silicon_professor.data.challenges import CHALLENGES
from silicon_professor.engine.challenges import challenge_design
from silicon_professor.engine.simulate import simulate


class TestChallenges(unittest.TestCase):
    def test_twelve_challenges_have_actual_failing_start_and_passing_solution(self):
        self.assertEqual(len(CHALLENGES),12)
        for sid,case in CHALLENGES.items():
            with self.subTest(case=sid):
                from silicon_professor.data.sources import SOURCES
                self.assertTrue(all(s in SOURCES for s in case['sources']))
                initial=simulate(challenge_design(sid))
                self.assertFalse(initial['challenge']['ready'])
                solved=simulate(challenge_design(sid,solution=True))
                self.assertTrue(solved['challenge']['ready'],solved['challenge'])
                self.assertTrue(solved['signoff']['ready'],solved['signoff']['blockers'])
                self.assertGreaterEqual(len(case['steps']),3)
                self.assertTrue(case['sources'])

    def test_challenge_can_travel_as_complete_sil(self):
        import tempfile
        from pathlib import Path
        from silicon_professor.export import export_to,read_design
        for sid in ('challenge_lab_cpu','challenge_camera','challenge_chiplet'):
            design=challenge_design(sid,solution=True)
            with tempfile.TemporaryDirectory() as td:
                file=export_to(Path(td)/'project.sil',design,simulate(design))
                replay,_=read_design(file)
                self.assertEqual(replay.scenario_id,sid)
                self.assertTrue(simulate(replay)['challenge']['ready'])
