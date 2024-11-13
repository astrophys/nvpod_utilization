# Author : Ali Snedden
# Date   : 09/18/24
#
# Copyright (C) 2024 Ali Snedden
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#
#
#
#
import os
import sys
import math
import random
import argparse
import datetime
import numpy as np
import pandas as pd
from collections import OrderedDict

class SacctObj :
    """Class that holds values entries from the sacct output. One line maps to one
       SacctObj object"""

    def __init__(self, jobid : int = None, jobname : str = None, nodelist : str = None,
                 elapsedraw : int = None, alloccpus : int = None,
                 cputimeraw : str = None, maxrss : str = None, state : str = None,
                 start : str = None, end : str = None):
        """Initialize SacctObj Class, contains only fields that that should be
           non-empty in sacct output

        Args :
            jobid       : jobid from the slurm job
            jobname     : name of job, can be batch or bash as well
            nodelist    : list of nodes
            elapsedraw  : elapsed / wall time in s
            alloccpus   : Number of cpus allocated
            cputimeraw  : alloccpus * elapsedraw = cpu time in s
            state       : COMPLETED,PENDING,FAILED,etc
            start       : Time in YYYY-MM-DDTHH:MM:SS
            end         : Time in YYYY-MM-DDTHH:MM:SS


        Returns :

        Raises :

        """
        self.jobid    = jobid
        self.jobname  = jobname
        self.nodelist = []
        if '[' in nodelist:
            stem = nodelist.split('[')[0]
            nodes = nodelist.split('[')[1]
            nodes = nodes.split(']')[0]
            nodes = nodes.split(',')
            # loop over node-ranges
            for nr in nodes :
                minnode = nr.split('-')[0].lstrip("0")
                maxnode = nr.split('-')[0].lstrip("0")
                tmp = ["{}0{}".format(stem,i) if i < 10 else "{}{}".format(stem,i) for i in range(int(minnode),int(maxnode)+1)]
                self.nodelist.append(tmp)
        else:
            self.nodelist.append(nodelist)
        if elapsedraw <= 10**-9:
            print("WARNING!!! Job {} has almost 0 elapsedraw time "
                  "{}".format(jobid, elapsedraw))
        self.elapsedraw = elapsedraw
        self.alloccpus  = alloccpus
        if not np.isclose(cputimeraw, alloccpus*elapsedraw):
            raise ValueError("ERROR!!! cputimeraw={}, alloccpus*elapsedraw={}".format(
                             cputimeraw,alloccpus*elapsedraw))
        self.cputimeraw = cputimeraw
        # MaxRSS
        if maxrss is None or len(maxrss) == 0:
            self.maxrss = None
        elif 'k' in maxrss.lower():
            self.maxrss = float(maxrss.lower().split('k')[0])
        elif 'm' in maxrss.lower():
            self.maxrss = float(maxrss.lower().split('m')[0])
        elif 'g' in maxrss.lower():
            self.maxrss = float(maxrss.lower().split('g')[0])
        elif 't' in maxrss.lower():
            self.maxrss = float(maxrss.lower().split('t')[0])
        else:
            raise ValueError("ERROR!!! Invalid value ({}) for maxrss".format(maxrss))
        # State
        if 'CANCELLED' in state:
            # Sometimes see things like 'CANCELLED by uid'
            self.state      = 'CANCELLED'
        else:
            self.state      = state
        # I don't understand when this condition occurs, seems stupid to me b/c I
        # have seen it with a valid 'end' time
        if start == 'None':
            self.start = None
        else:
            try :
                self.start = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S")
            except TypeError:
                self.start = start
        if state != 'RUNNING' :
            try :
                self.end  = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")
            except TypeError:
                self.end = end
        else:
            self.end        = None
        # Sanity check
        if self.start is not None and self.end is not None:
            if self.start > self.end:
                raise ValueError("ERROR!!! self.start ({}) > self.end ({}), makes "
                                 "no sense".format(self.start,self.end))


    # https://stackoverflow.com/a/47625174/4021436
    def as_dict(self):
        """Return self's variables as dictionary s.t. it can be easily converted to
           a pandas data frame.

        Args :

        Returns :

        Raises :

        """
        if self.end is None:
            end = 'Unknown'
        else:
            end = "{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(self.end.year,
                  self.end.month, self.end.day, self.end.hour, self.end.minute,
                  self.end.second)
        start = "{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(self.start.year,
                  self.start.month, self.start.day, self.start.hour,
                  self.start.minute, self.start.second)
        maxrss = "{}K".format(int(self.maxrss))
        return OrderedDict([
                ("JobID", self.jobid), ("JobName", self.jobname), ("User", ""),
                ("NodeList", ','.join(self.nodelist)), ("ElapsedRaw", self.elapsedraw),
                ("AllocCPUS", self.alloccpus), ("CPUTimeRAW", self.cputimeraw),
                ("MaxRSS", maxrss), ("State", self.state),
                ("Start", start),("End", end),
                ("ReqTRES", "")
                           ])


class Job(SacctObj) :
    """Class that maps to a single Slurm job"""

    def __init__(self, jobid : int = None, jobname : str = None, user : str = None,
                 nodelist : str = None, elapsedraw : int = None,
                 alloccpus : int = None, cputimeraw : str = None, maxrss : str = None,
                 state : str = None, start : str = None, end : str = None,
                 reqtres : str = None):

        """Initialize Job Class

        Args :

        Returns :

        Raises :

        """
        # https://stackoverflow.com/a/5166588/4021436
        SacctObj.__init__(self, jobid = jobid, jobname = jobname, nodelist = nodelist,
                          elapsedraw = elapsedraw, alloccpus = alloccpus,
                          cputimeraw = cputimeraw, maxrss = maxrss, state = state,
                          start = start, end = end)
        self.user = user
        self.reqtres = reqtres
        # Set these PRIOR to parsing reqtres in case no GPUs were present
        self.ngpu       = 0
        self.gputimeraw = 0
        for substr in reqtres.split(','):
            tresL = substr.split('=')
            if tresL[0] == 'billing':
                self.reqtresbilling = int(tresL[1])
            # It is very hard to understand exactly how reqtrescpu is calculated
            # $ srun --nodes=2 --ntasks-per-node=8 --gpus-per-node=8 --cpus-per-gpu=6
            #        --pty bash
            # Yields alloccpus=96, but reqtres = billing=16,cpu=16,gres/gpu=16
            #
            # $ srun --nodes=2 --ntasks-per-node=8 --gpus-per-node=8 --cpus-per-task=6
            #        --pty bash
            # Yields alloccpus=96, but reqtres = billing=96,cpu=96,gres/gpu=16
            #
            # Clearly reqtrescpu is fickle in interpretting, I don't understand why
            # two ostensibly identical jobs, yielded different reqtres cpu
            if tresL[0] == 'cpu':
                self.reqtrescpu = int(tresL[1])
            if tresL[0] == 'gres/gpu':
                self.reqtresgpu = int(tresL[1])
                self.ngpu       = int(tresL[1])
                self.gputimeraw = self.ngpu * self.elapsedraw
            if tresL[0] == 'mem':
                if 'M' in tresL[1]:
                    mem = int(tresL[1].split('M')[0]) / 1024
                elif 'G' in tresL[1]:
                    mem = int(tresL[1].split('G')[0])
                elif 'T' in tresL[1]:
                    mem = int(tresL[1].split('T')[0]) * 1024
                elif 'K' in tresL[1]:
                    mem = int(tresL[1].split('K')[0]) / 1024**2
                else:
                    raise ValueError("ERROR!! Unexpected memory units in tres : {}".format(tresL[1]))
                self.reqtresmemgb = mem
            if tresL[0] == 'node':
                self.reqtresnode = int(tresL[1])
        self.stepL = []
        self.externL = []
        self.batchL = []


    # https://stackoverflow.com/a/47625174/4021436
    def as_dict(self):
        """Return self's variables as dictionary s.t. it can be easily converted to
           a pandas data frame.

        Args :

        Returns :

        Raises :

        """
        if self.end is None:
            end = 'Unknown'
        else:
            end = "{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(self.end.year,
                  self.end.month, self.end.day, self.end.hour, self.end.minute,
                  self.end.second)
        start = "{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(self.start.year,
                  self.start.month, self.start.day, self.start.hour,
                  self.start.minute, self.start.second)
        maxrss = "{}K".format(int(self.maxrss))
        return OrderedDict([
                ("JobID", self.jobid), ("JobName", self.jobname), ("User", self.user),
                ("NodeList", ','.join(self.nodelist)), ("ElapsedRaw", self.elapsedraw),
                ("AllocCPUS", self.alloccpus), ("CPUTimeRAW", self.cputimeraw),
                ("MaxRSS", maxrss), ("State", self.state),
                ("Start", start),("End", end),
                ("ReqTRES", self.reqtres)])
    #def write(self)


class Step(SacctObj) :
    """Class that maps to a single Slurm step"""

    def __init__(self, step : int = None, jobid : int = None, jobname : str = None,
                 nodelist : str = None, elapsedraw : int = None,
                 alloccpus : int = None, cputimeraw : str = None, state : str = None,
                 start : str = None, end : str = None):

        """Initialize Step Class

        Args :

        Returns :

        Raises :

        """
        # https://stackoverflow.com/a/5166588/4021436
        SacctObj.__init__(self, jobid = jobid, jobname = jobname, nodelist = nodelist,
                          elapsedraw = elapsedraw, alloccpus = alloccpus,
                          cputimeraw = cputimeraw, state = state, start = start,
                          end = end)
        self.step = step


class User :
    """Class that holds info for an individual user"""

    def __init__(self, name : str = None, njobs : int = None, cputimeraw : int = None,
                 gputimeraw : int = None):

        """Initialize User Class

        Args :

        Returns :

        Raises :

        """
        self.name = name
        self.njobs = njobs
        self.cputimeraw = cputimeraw        # in s
        self.gputimeraw = gputimeraw        # in s

