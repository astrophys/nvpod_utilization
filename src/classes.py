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
from typing import List
from bisect import bisect_left
from collections import OrderedDict


class SacctObj :
    """Class that holds values entries from the sacct output. One line maps to one
       SacctObj object"""

    def __init__(self, jobid : int = None, jobname : str = None, nodelist : str = None,
                 elapsedraw : int = None, alloccpus : int = None,
                 cputimeraw : str = None, maxrss : str = None, state : str = None,
                 start : str = None, end : str = None, Verbose : bool = False):
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
            # loop over node-ranges, like node[06-08,13,24-29]
            for nr in nodes :
                # handle cases like node[06-09]
                if '-' in nr:
                    minnode = nr.split('-')[0].lstrip("0")
                    maxnode = nr.split('-')[1].lstrip("0")
                    tmp = ["{}0{}".format(stem,i) if i < 10 else "{}{}".format(stem,i) for i in range(int(minnode),int(maxnode)+1)]
                    self.nodelist.extend(tmp)
                # handle cases like node[06]
                else :
                    tmp = "{}{}".format(stem,nr)
                    self.nodelist.append(tmp)
        else:
            self.nodelist.append(nodelist)
        if elapsedraw <= 10**-9 and Verbose is True :
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


class Util :
    """Class that maps entry in a node*_gpuutil_gpu*.txt"""

    def __init__(self, line : str = None):

        """Initialize Util(ization) Class

        Args :
            line = line with date and utilization in node*_gpuutil_gpu*.txt files

        Returns :
            Util class

        Raises :
            ValueError when unexpected line format is encountered

        """
        strL = line.split()
        datestr = " ".join(strL[0:2])
        datestr = datestr.split('.')[0]
        self.time = datetime.datetime.strptime(datestr, "%Y/%m/%d %H:%M:%S")
        try :
            #self.date = datetime.datetime.strptime(datestr, "%Y/%m/%d %H:%M:%S")
            self.util = float(strL[2].split('%')[0])
        except ValueError :
            ## If no data, set to invalid value
            if 'no data' in line.lower():
                self.util = -1
            else :
                raise ValueError("ERROR!!! Parsing line = {}".format(line))


    # https://stackoverflow.com/a/4010558/4021436
    def __lt__(self, other):

        """Utility used for sorting objects

        Args :
            other : Another Util object

        Returns :
            bool based on which is used

        Raises :
        """
        return self.time < other.time


class Gpu :
    """Class that maps to a single Slurm job"""

    def __init__(self, gpupath : str = None):

        """Initialize Gpu Class

        Args :

        Returns :

        Raises :
            ValueError if the utilization is not sorted by date

        """
        fin = open(gpupath, 'r')
        if 'totalgpuutilization' not in gpupath:
            gidx = gpupath.split("/")[-1]
            gidx = gidx.split(".")[0]
            gidx = gidx.split("gpu")[-1]
            gidx = int(gidx.split("_")[0])
            self.gidx = gidx
        else :
            self.gidx = -1
        self.utilL = []
        self.healthy = True
        for line in fin:
            if line[0] == '#':
                strL = line.split()
                datestr = " ".join(strL[4:8])
                datestr = datestr.split('.')[0]

                # https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
                if 'Start' in line :
                    self.start = datetime.datetime.strptime(datestr, "%b %d %H:%M:%S %Y")
                if 'End' in line :
                    self.end= datetime.datetime.strptime(datestr, "%b %d %H:%M:%S %Y")
            else :
                util = Util(line)
                self.utilL.append(util)
        if self.is_sorted(self.utilL) == False:
            raise ValueError("ERROR!!! {} has unsorted gpu utilization".format(gpupath))
        fin.close()


    def is_sorted(self, utilL : List[Util] = None) -> bool :
        """Test to see if sorted

        Args :
            utilL : List of Util objects

        Returns :
            bool on if it is sorted or not

        Raises :
        """
        tmpL = sorted(utilL)
        return tmpL == utilL


    def mean_util_over_interval(self, start : datetime.datetime = None,
                                end : datetime.datetime = None,
                                Verbose : bool = True) -> float :
        """Calculate average utilization for gpu over some time interval

        Args :
            start : start of interval
            end   : end of interval

        Returns :
            (float) of average utilization over a time interval

        Raises :
        """
        # self.utilL must be sorted for this to work
        # https://stackoverflow.com/a/2701189/4021436


        #for util in self.utilL:

        print('the end')


class Node :
    """Take list of gpuutil files, read in and allocate gpus"""

    def __init__(self, gpupathL : str = None):
        """Initialize Node Class,

        Args :
            gpuL = list of node*_gpuutil_*.txt files, used to allocate Gpu class and
                   read the data

        Returns :

        Raises :

        """
        self.gpuL = []
        name = gpupathL[0].split("/")[-1]
        consolidator = (name.split('_')[3]).split('.')[0]
        name = name.split("_")[0]
        self.name = name
        for gpupath in gpupathL:
            gpu = Gpu(gpupath)
            if gpu.healthy is False :
                print("{} : gpu{}".format(self.name, gpu.gidx))
            self.gpuL.append(gpu)
        # Set consolidator
        self.consolidator = consolidator


    def calc_util_over_interval(self, start : datetime.datetime = None,
                                end : datetime.datetime = None):
        """Calculate average utilization for entire node over some time interval

        Args :
            gpuL = list of node*_gpuutil_*.txt files, used to allocate Gpu class and
                   read the data

        Returns :

        Raises :

        """
        total = 0
        for gpu in self.gpuL:
            gpumeanutil = gpu.mean_util_over_interval(start, end)
            total += gpumeanutil
        print('the end again')



class TotalGpu :
    """Take totalgpuutilization_1d.txt, read it"""

    def __init__(self, path : str = None):

        """Initialize Total Class,

        Args :
            path = path to total gpu utilization

        Returns :

        Raises :

        """
        name = path.split("/")[-1]
        consolidator = name.split('_')[-1].split('.')[0]
        #name = name.split("_")[0]
        self.name = name
        self.consolidator = consolidator
        # Isn't really a GPU, but the file is basically the same.
        self.totalgpu = Gpu(path)
        # Set consolidator


class Cluster :
    """Take list of Nodes"""

    def __init__(self, nodeL : List[Node] = None, totalpath : str = None):

        """Initialize Cluster Class,

        Args :
            gpuL = list of node*_gpuutil_*.txt files, used to allocate Gpu class and
                   read the data

        Returns :

        Raises :

        """
        self.nodeL = nodeL
        self.total = TotalGpu(totalpath)


    def validate(self):

        """Validate that the total GPU is the the average across all nodes

        Args :

        Returns :

        Raises :

        """

