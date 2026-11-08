import unittest

from silicon_professor.data.lab_courses import COURSES, evaluate_course
from silicon_professor.engine.labs import run_experiment


class TestLabCourses(unittest.TestCase):
    def test_each_course_has_unsolved_initial_and_verified_solution(self):
        for course in COURSES:
            with self.subTest(course=course["id"]):
                a = course["initial"]
                b = course["solution"]
                self.assertFalse(all(evaluate_course(course, a, run_experiment(course["kind"], a))))
                self.assertTrue(all(evaluate_course(course, b, run_experiment(course["kind"], b))))
                self.assertTrue(course["sources"])
                self.assertGreater(len(course["lecture"]), 150)


if __name__ == "__main__": unittest.main()
