# Author : Ali Snedden
# Date   : 09/18/24
# License:
#
#
#
#
#
#
import os
import sys
import random
import argparse
import numpy as np
import pandas as pd

class SacctObj :
    """Class that holds values entries from the sacct output. One line maps to one
       SacctObj object"""

    def __init__(self, jobid : int = None, jobname : str = None, nodelist : str = None,
                 elapsedraw : int = None, alloccpus : int = None,
                 cputimeraw : str = None, state : str = None, start : str = None,
                 end : str = None)

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
            for nr in node :
                minnode = nr.split('-')[0].lstrip("0")
                maxnode = nr.split('-')[0].lstrip("0")
                tmp = ["{}0{}".format(stem,i) if i < 10 else "{}{}".format(stem,i) for i in range(int(minnode),int(maxnode)+1)]
                self.nodelist.append(tmp)
        else:
            self.nodelist.append(nodelist)
        self.elapsedraw = elapsedraw
        self.alloccpus  = alloccpus
        if not np.isclose(cputimeraw, alloccpus*elapsedraw):
            raise ValueError("ERROR!!! cputimeraw={}, alloccpus*elapsedraw={}".format(
                             cputimeraw,alloccpus*elapsedraw))
        self.cputimeraw = cputimeraw
        self.state      = state
        self.start      = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S")
        self.end        = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")




class Step(SacctObj) :
    """Class that maps to a single Slurm step"""

    def __init__(self)

        """Initialize Step Class

        Args :

        Returns :

        Raises :

        """


class Batch(SacctObj) :
    """Class that maps to the batch script of a Slurm job"""

    def __init__(self, )

        """Initialize Job Class

        Args :

        Returns :

        Raises :

        """

class Job :
    """Class that maps to a single Slurm job"""

    def __init__(self)

        """Initialize Job Class

        Args :

        Returns :

        Raises :

        """

        self.step = []



class Measurable :
    """Class that maps to a BCM measurable"""

    def __init__(self, producer : str = None, )

        """Initialize Job Class

        Args :

        Returns :

        Raises :

        """

        self.step = []






