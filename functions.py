import os
import sys
import random
import datetime
import numpy as np
import pandas as pd

# Parses output created by :
#   sacct -p -a -S 2024-09-01 --format="job,jobname,user,node,elapsedraw,alloccpus,cputimeraw,maxrss,state,start,end,reqtres"
# In sacct :
#   1. Most job entries 3 entris
#       a) There is a toplevel is the job
#           #. Only line that has a username and a non-entry for reqtres
#       #)
#
def parse_sacct_file(path : str = None):
    """Takes output from sacct in parsable mode, returns stuff

    Args


    Returns

    Raises

    """
    df = pd.read_csv(path)
    ## group by jobid, strip off '.ext', '.batch' and step number appende by sact
    jobnum = df['JobID'].str.split('.', expand=True)[0]
    df['jobnum'] = jobnum
    ## Get unique job numbers
    uniqjobnumV = np.unique(df['JobID'].str.split('.', expand=True)[0])

    for job in 



def string2time(string : str = None):
    """Takes string in format YYYY-MM-DDTHH:MM:SS to a Python time

    Args
        string : time in format YYYY-MM-DDTHH:MM:SS

    Returns

    Raises

    """
    return datetime.datetime.strptime(string, "%Y-%m-%dT%H:%M:%S")

