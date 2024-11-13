# Author : Ali Snedden
# Date   : 11/11/24
# License: GPL-3
"""Module that unit tests the module is_job_in_time_range()
"""
import unittest
import numpy as np
import datetime
from classes import Job
from functions import is_job_in_time_range
from functions import parse_sacct_file


class TEST_PARSE_SACCT_FILE(unittest.TestCase):
    """
    Test to see that parse_sacct_file()'s logic works

    Args:
        unittest.TestCase

    Returns:
        N/A
    """
    def test_parse_sacct_file(self):
        """
        Checks for equality in several cases

        Args:
            self :

        Returns:
            N/A
        """
        (totalgpuraw, totalcpuraw, jobL, starttime, endtime) = parse_sacct_file(path='data/test_data.txt')
        # Got below values from running
        #   python src/make_fake_data.py  --output data/test_data.txt
        self.assertEqual(0+50000+120000, totalgpuraw)
        self.assertEqual(120000+150000+180000, totalcpuraw)


if __name__ == "__main__":
    unittest.main()
    # Exit value handled by unittest.main()
