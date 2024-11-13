# Author : Ali Snedden
# Date   : 09/18/24
# Goals (ranked by priority) :
#
# Refs :
#   a)
#   #) https://stackoverflow.com/a/14992648/4021436
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
import os
import sys
import random
from random import randint
import argparse
import datetime
import operator
import numpy as np
import pandas as pd
import matplotlib
#matplotlib.use('tkagg')        # Linux
matplotlib.use('qtagg')        # Linux
from classes import User,Job,SacctObj
import matplotlib.pyplot as plt
from plot_funcs import make_pie
from plot_funcs import plot_time_series
from functions import make_autopct
from functions import is_job_in_time_range


# Expects data like : sacct --allusers -P -S 2024-08-01 --format="jobid,jobname,user,nodelist,elapsedraw,alloccpus,cputimeraw,maxrss,state,start,end,reqtres" > sacct_2024-08-01.txt

# Run via
#   python -m pdb bcm_accounting_plots.py --path data/sacct_2024-09-01_to_2024-10-16.txt --start 2024-08-30T00:00:00 --end 2024-10-15T00:00:00 --plottype time-series
def main():
    """Loads the sacct .

    Args

        N/A

    Returns

    Raises

    """

    parser = argparse.ArgumentParser(
                    description="This generates plots from output of `sacct`")
    parser.add_argument('--output', metavar='path/to/outputfile', type=str,
                        help='Path to output file')
    #parser.add_argument('--start', metavar='starttime', type=str,
    #                    help='Time in YYYY-MM-DDTHH:MM:SS format')
    #parser.add_argument('--end', metavar='enddate', type=str,
    #                    help='Time in YYYY-MM-DDTHH:MM:SS format')
    #parser.add_argument('--plottype', metavar='plottype', type=str,
    #                    help='Options : "histogram", "pie" or "time-series"')
    #parser.add_argument('--users', metavar='users', type=str,
    #                    help='Options : "all", "total" or "someuser"')
    #parser.add_argument('--plottype', metavar='plottype', type=str,
    #                    help='Options : "histogram", "pie" or "time-series"')
    random.seed(42)
    args = parser.parse_args()
    outpath = args.output
    ### Assume 4 DGX nodes with 8 GPUs and 224 cores each
    jobL = []
    njob = 10       # number of jobs per user
    state = ['RUNNING', 'COMPLETED', 'CANCELLED', 'CANCELLED by 123', 'NODE_FAIL', 'FAILED']
    ##
    begindate    = datetime.datetime(2024,10,1)
    enddate      = datetime.datetime(2024,11,1)
    totalsec     = (enddate - begindate).total_seconds()
    userL        = ['bill', 'anna', 'ryan']
    #userfracL   = [  0.33,   0.66,    1.0]
    startelapsedL = [40000,  50000,  60000]
    remainelapsedL = startelapsedL.copy()
    usergputimeL = [     0,      0,      0]
    nodeL        = [ 'n01',  'n02',  'n03', 'n04']
    scriptnameL  = [ 'foo.sh', 'bar.sh', 'hello.sh']
    maxcpu       = 32       # Maximum number of available cpus on node
    maxgpu       = 8        # Maximum number of available cpus on node
    nuser = len(userL)
    maxrss = '1000000K'     # Max mem
    maxnodemem = '2063937M'     # Recall that mem isn't a tracked resource..
    ncpu = 3
    jobid=1
    jobname='stuff'

    for uidx in range(len(userL)):
        user = userL[uidx]

        for j in range(njob):
            jobid += 1
            # total time remaining
            remain   = remainelapsedL[uidx]
            ngpu     = uidx                     #randint(0, maxgpu+1)
            # Ensure AT LEAST one job is running
            if j == 0:
                rng = randint(0,120)
                jobstart = enddate - datetime.timedelta(seconds=rng)
                tdelta = datetime.timedelta(seconds=randint(rng, int(totalsec)))
            # Last job, make sure to use ALL of the time
            elif j == njob - 1:
                tdelta   = datetime.timedelta(seconds=remain)
                jobstart = enddate - tdelta
            else:
                # Get job start time
                jobstart = begindate + datetime.timedelta(seconds=
                                                          randint(0, int(totalsec)))
                # Get job run time
                rng      = randint(0, int(remain))# + randint(0, 100)
                tdelta   = datetime.timedelta(seconds=rng)

            # Get state
            if jobstart + tdelta > enddate:
                state = 'RUNNING'
                jobend = 'Unknown'
                elapsed = (enddate - jobstart).total_seconds()
                print("j={} {} {} {}".format(j, user, remainelapsedL[uidx], elapsed))
                remainelapsedL[uidx] -= elapsed
            else:
                state = 'COMPLETED'
                jobend = jobstart + tdelta
                elapsed = (jobend - jobstart).total_seconds()
                usergputimeL[uidx] += elapsed * ngpu
                print("j={} {} {} {}".format(j, user, remainelapsedL[uidx], elapsed))
                remainelapsedL[uidx] -= elapsed

            nodelist = nodeL[uidx]
            nnode = 1

            #ncpu = randint(0, maxcpu)
            # Recall that computing reqtrescpu is confusing and non-intuitive,
            # obviously I'm not accurately computing it here.  All I care about is
            # the number of GPUs
            reqtres = "billing={},cpu={},gres/gpu={},mem={},node={}".format(ncpu, ncpu,
                      ngpu, maxnodemem, nnode)
            cputimeraw = ncpu * elapsed
            elapsedraw = elapsed

            # Naturally, I'd put the steps / batch into the job.[step,batch]L
            # However to easily to put this into a data frame per
            # https://stackoverflow.com/a/47625174/4021436
            # I'm going to put them all in the 'jobL' to make my life easier and to
            # avoid having to write a 'print' function in the JobL class
            job = Job(jobid=jobid, jobname=jobname, user=user, nodelist=nodelist,
                      elapsedraw=elapsedraw, alloccpus=ncpu, cputimeraw=cputimeraw,
                      maxrss=maxrss, state=state, start=jobstart, end=jobend,
                      reqtres=reqtres)
            jobL.append(job)
            ## Batch
            batch = SacctObj(jobid="{}.batch".format(jobid), jobname='batch',
                             nodelist=nodelist, elapsedraw=elapsedraw, alloccpus=ncpu,
                             cputimeraw=cputimeraw, maxrss=maxrss, state=state,
                             start=jobstart, end=jobend)
            #job.batchL.append(batch)
            jobL.append(batch)
            ## Step
            step = SacctObj(jobid="{}.0".format(jobid), jobname=jobname,
                       nodelist=nodelist, elapsedraw=elapsedraw, alloccpus=ncpu,
                       cputimeraw=cputimeraw, maxrss=maxrss, state=state,
                       start=jobstart, end=jobend)
            #job.stepL.append(step)
            jobL.append(step)
            #jobL.append(job)

    ## Let's print out to validate my code
    elapsedtimeL=[0, 0, 0]
    gpurawL =[0, 0, 0]
    cpurawL =[0, 0, 0]
    for job in jobL:
        if type(job) == Job:
            user = job.user
            uidx = 0
            # Get correct uidx
            for uidx in range(len(userL)):
                if userL[uidx] == user:
                    break
            elapsedtimeL[uidx] += job.elapsedraw
            cpurawL[uidx] += job.cputimeraw
            gpurawL[uidx] += job.gputimeraw
    print("Job match : ")
    print("\tjob elapsed = {}".format(elapsedtimeL))     # Gets close
    print("\tjob cpu raw = {}".format(cpurawL))     # Gets close
    print("\tjob gpu raw = {}".format(gpurawL))     # Gets close
    print("Should match : ")
    print("\telapsed = {}".format(startelapsedL))
    print("\tcpu raw = [{} {} {}]".format(startelapsedL[0] * ncpu,
          startelapsedL[1] * ncpu, startelapsedL[2] * ncpu,))
    print("\tgpu raw = [{} {} {}]".format(startelapsedL[0] * 0,
          startelapsedL[1] * 1, startelapsedL[2] * 2))

    # Really looping over both SacctObj and Job objects
    df = pd.DataFrame([job.as_dict() for job in jobL])
    df.to_csv(outpath, sep='|', index=False)
    ## Extract by time range
    sys.stdout.flush()
    sys.exit(0)


if __name__ == "__main__":
    main()


