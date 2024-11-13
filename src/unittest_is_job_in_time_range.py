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


class TEST_IS_JOB_IN_TIME_RANGE(unittest.TestCase):
    """
    Test to see that is_job_in_time_range()'s logic works

    Args:
        unittest.TestCase

    Returns:
        N/A
    """
    def test_is_job_in_time_range(self):
        """
        Checks for equality in several cases

        Args:
            self :

        Returns:
            N/A
        """
        ##### Test 1
        #  timerange :                     mintime    maxtime
        #                                    |-----------|
        #  job       :     |------------|
        #               job.start    job.end
        elapsedraw = 1*24*60*60              # 1 day In seconds
        jobstart = '2024-11-01T08:00:00'
        jobend   = '2024-11-02T08:00:00'
        # Time frame
        mintime = '2024-11-03T08:00:00'
        maxtime = '2024-11-04T08:00:00'
        mintime = datetime.datetime.strptime(mintime, "%Y-%m-%dT%H:%M:%S")
        maxtime = datetime.datetime.strptime(maxtime, "%Y-%m-%dT%H:%M:%S")
        #
        truth = False
        job = Job(jobid=1, jobname='test', user='maggie', nodelist='node01',
                  elapsedraw=elapsedraw, alloccpus=32,
                  cputimeraw=32*elapsedraw, maxrss='10M',
                  state='R', start=jobstart, end=jobend,
                  reqtres='billing=1,cpu=1,gres/gpu=1,mem=2063937M,node=1')
        inrange,overlap = is_job_in_time_range(job=job, mintime=mintime,
                                               maxtime=maxtime)
        self.assertFalse(inrange)
        self.assertEqual(0, overlap)


        ##### Test 2
        #  timerange : mintime    maxtime
        #                |-----------|
        #  job       :                   |--------------|
        #                             job.start      job.end
        elapsedraw = 1*24*60*60              # 1 day In seconds
        jobstart = '2024-11-01T08:00:00'
        jobend   = '2024-11-02T08:00:00'
        # Time frame
        mintime = '2024-10-30T08:00:00'
        maxtime = '2024-10-31T08:00:00'
        mintime = datetime.datetime.strptime(mintime, "%Y-%m-%dT%H:%M:%S")
        maxtime = datetime.datetime.strptime(maxtime, "%Y-%m-%dT%H:%M:%S")
        #
        truth = False
        job = Job(jobid=1, jobname='test', user='maggie', nodelist='node01',
                  elapsedraw=elapsedraw, alloccpus=32,
                  cputimeraw=32*elapsedraw, maxrss='10M',
                  state='R', start=jobstart, end=jobend,
                  reqtres='billing=1,cpu=1,gres/gpu=1,mem=2063937M,node=1')
        inrange,overlap = is_job_in_time_range(job=job, mintime=mintime,
                                               maxtime=maxtime)
        self.assertFalse(inrange)
        self.assertEqual(0, overlap)


        ##### Test 3
        #  timerange :          mintime          maxtime
        #                          |---------------|
        #  job       :    |----------------|
        #             job.start         job.end
        elapsedraw = 1*24*60*60              # 1 day In seconds
        jobstart = '2024-11-01T08:00:00'
        jobend   = '2024-11-02T08:00:00'
        # Time frame
        mintime = '2024-11-01T20:00:00'
        maxtime = '2024-11-03T08:00:00'
        mintime = datetime.datetime.strptime(mintime, "%Y-%m-%dT%H:%M:%S")
        maxtime = datetime.datetime.strptime(maxtime, "%Y-%m-%dT%H:%M:%S")
        #
        truth = False
        job = Job(jobid=1, jobname='test', user='maggie', nodelist='node01',
                  elapsedraw=elapsedraw, alloccpus=32,
                  cputimeraw=32*elapsedraw, maxrss='10M',
                  state='R', start=jobstart, end=jobend,
                  reqtres='billing=1,cpu=1,gres/gpu=1,mem=2063937M,node=1')
        inrange,overlap = is_job_in_time_range(job=job, mintime=mintime,
                                               maxtime=maxtime)
        self.assertTrue(inrange)
        self.assertEqual(12*60*60, overlap.total_seconds())


        ##### Test 4
        #  timerange :    mintime          maxtime
        #                    |---------------|
        #  job       :               |----------------|
        #                        job.start         job.end
        elapsedraw = 1*24*60*60              # 1 day In seconds
        jobstart = '2024-11-01T08:00:00'
        jobend   = '2024-11-02T08:00:00'
        # Time frame
        mintime = '2024-11-01T00:00:00'
        maxtime = '2024-11-01T12:00:00'
        mintime = datetime.datetime.strptime(mintime, "%Y-%m-%dT%H:%M:%S")
        maxtime = datetime.datetime.strptime(maxtime, "%Y-%m-%dT%H:%M:%S")
        #
        truth = False
        job = Job(jobid=1, jobname='test', user='maggie', nodelist='node01',
                  elapsedraw=elapsedraw, alloccpus=32,
                  cputimeraw=32*elapsedraw, maxrss='10M',
                  state='R', start=jobstart, end=jobend,
                  reqtres='billing=1,cpu=1,gres/gpu=1,mem=2063937M,node=1')
        inrange,overlap = is_job_in_time_range(job=job, mintime=mintime,
                                               maxtime=maxtime)
        self.assertTrue(inrange)
        self.assertEqual(4*60*60, overlap.total_seconds())


        ##### Test 5
        #  timerange :              mintime          maxtime
        #                             |-----------------|
        #  job       :          |-------------------------------|
        #                    job.start                        job.end
        elapsedraw = 1*24*60*60              # 1 day In seconds
        jobstart = '2024-11-01T08:00:00'
        jobend   = '2024-11-02T08:00:00'
        # Time frame
        mintime = '2024-11-01T09:00:00'
        maxtime = '2024-11-02T07:00:00'
        mintime = datetime.datetime.strptime(mintime, "%Y-%m-%dT%H:%M:%S")
        maxtime = datetime.datetime.strptime(maxtime, "%Y-%m-%dT%H:%M:%S")
        #
        truth = False
        job = Job(jobid=1, jobname='test', user='maggie', nodelist='node01',
                  elapsedraw=elapsedraw, alloccpus=32,
                  cputimeraw=32*elapsedraw, maxrss='10M',
                  state='R', start=jobstart, end=jobend,
                  reqtres='billing=1,cpu=1,gres/gpu=1,mem=2063937M,node=1')
        inrange,overlap = is_job_in_time_range(job=job, mintime=mintime,
                                               maxtime=maxtime)
        self.assertTrue(inrange)
        self.assertEqual(22*60*60, overlap.total_seconds())


        ##### Test 6
        #  timerange :  mintime                         maxtime
        #                 |--------------------------------|
        #  job       :          |-----------------|
        #                    job.start         job.end
        elapsedraw = 1*24*60*60              # 1 day In seconds
        jobstart = '2024-11-01T08:00:00'
        jobend   = '2024-11-02T08:00:00'
        # Time frame
        mintime = '2024-10-31T09:00:00'
        maxtime = '2024-11-03T07:00:00'
        mintime = datetime.datetime.strptime(mintime, "%Y-%m-%dT%H:%M:%S")
        maxtime = datetime.datetime.strptime(maxtime, "%Y-%m-%dT%H:%M:%S")
        #
        truth = False
        job = Job(jobid=1, jobname='test', user='maggie', nodelist='node01',
                  elapsedraw=elapsedraw, alloccpus=32,
                  cputimeraw=32*elapsedraw, maxrss='10M',
                  state='R', start=jobstart, end=jobend,
                  reqtres='billing=1,cpu=1,gres/gpu=1,mem=2063937M,node=1')
        inrange,overlap = is_job_in_time_range(job=job, mintime=mintime,
                                               maxtime=maxtime)
        self.assertTrue(inrange)
        self.assertEqual(24*60*60, overlap.total_seconds())



if __name__ == "__main__":
    unittest.main()
    # Exit value handled by unittest.main()
