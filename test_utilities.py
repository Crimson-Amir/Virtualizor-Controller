import unittest
from utilities import *
from datetime import datetime


class UtilitiesTest(unittest.TestCase):
    def test_report_problem_to_admin(self):
        self.assertEqual(report_problem_to_admin('This is test message from unittest').status_code, 200)

    def test_replace_with_space(self):
        self.assertEqual(replace_with_space('Test_Message'), 'Test Message')

    def test_human_readable(self):
        self.assertIsInstance(human_readable(datetime.now()), str)

    def test_unix_time_to_datetime(self):
        self.assertEqual(str(unix_time_to_datetime(1453714166)), '2016-01-25 12:59:26')


if __name__ == '__main__':
    unittest.main()