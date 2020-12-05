'''
Copyright 2020, Cray Inc., A Hewlett Packard Enterprise Company
'''
import unittest
import batcher


class InfrastructureTest(unittest.TestCase):
    def test_working_infrastructure(self):
        """
        The purpose of this test is to show the testing infrastructure works; this should always pass
        with success; if it doesn't, then something is amiss with the testing setup for the project.
        """
        self.assertTrue(True, "True is true!")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
