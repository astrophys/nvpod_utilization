# Author : Ali Snedden
# Date   : 09/18/24
# Goals (ranked by priority) :
#
# Refs :
#   a)
#   #) https://www.nltk.org/book/ch06.html
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
import argparse
import datetime
import operator
import numpy as np
import pandas as pd
import matplotlib
#matplotlib.use('tkagg')        # Linux
matplotlib.use('qtagg')        # Linux
from classes import User
import matplotlib.pyplot as plt
from plot_funcs import make_pie
from plot_funcs import plot_time_series_mpl
from plot_funcs import plot_time_series_plotly
from functions import make_autopct
from functions import parse_sacct_file
from functions import is_job_in_time_range


# Expects data like : sacct --allusers -P -S 2024-08-01 --format="jobidraw,jobname,user,nodelist,elapsedraw,alloccpus,cputimeraw,maxrss,state,start,end,reqtres" > sacct_2024-08-01.txt

# Run via
#    python -m pdb src/bcm_accounting_plots.py --path data/sacct_2024-05-01_to_2024-10-31.txt --start 2024-05-01T00:00:00 --end 2024-11-01T00:00:00 --plottyp time-series --users all
def main():
    """Loads the sacct .

    Args

        N/A

    Returns

    Raises

    """
    parser = argparse.ArgumentParser(
                    description="This generates plots from output of `sacct`")
    parser.add_argument('--path', metavar='path/to/sacct_text_file', type=str,
                        help='Path to parsable sacct file')
    parser.add_argument('--start', metavar='starttime', type=str,
                        help='Time in YYYY-MM-DDTHH:MM:SS format')
    parser.add_argument('--end', metavar='endtime', type=str,
                        help='Time in YYYY-MM-DDTHH:MM:SS format')
    parser.add_argument('--plottype', metavar='plottype', type=str,
                        help='Options : "histogram", "pie" or "time-series"')
    parser.add_argument('--users', metavar='users', type=str,
                        help='Options : "all", "total", "total_alloc+util", or '
                        '"someuser"')
    parser.add_argument('--engine', metavar='engine', type=str,
                        help='Options : "plotly" or "matplotlib" (default)')
    parser.add_argument('--totalutil_1d', metavar='path/to/gpuutilization_1d',
                        type=str, help='Path to many gpu utilization')
    args = parser.parse_args()
    path = args.path
    users = args.users
    plottype = args.plottype
    totalutil1d = args.totalutil_1d
    engine = args.engine
    if engine is None :
        engine = 'matplotlib'
    mintime = datetime.datetime.strptime(args.start, "%Y-%m-%dT%H:%M:%S")
    maxtime = datetime.datetime.strptime(args.end, "%Y-%m-%dT%H:%M:%S")
    walltime = maxtime - mintime
    walltime = walltime.total_seconds()
    print("Time Range : ")
    print("\t {}".format(mintime))
    print("\t {}".format(maxtime))
    #### System specific information
    nnodes = 31
    ngpupernode = 8
    ncpupernode = 224       # Threads in case of multithreading

    #df = pd.read_csv(path, sep='|')
    (_, _, jobL, starttime, endtime) = parse_sacct_file(path=path)

    # total time avail

    if plottype == 'pie':
        ## Extract by user
        userL = []
        usernameL = np.unique([job.user for job in jobL])
        for username in usernameL:
            njob = 0
            cputimeraw = 0
            gputimeraw = 0
            # Extracts ANY job that has ANY part fall w/in the [mintime, maxtime]
            for job in jobL:
                if username == job.user:
                    inrange,overlap = is_job_in_time_range(job, mintime, maxtime)
                    if inrange is True and job.elapsedraw > 0:
                        njob += 1
                        #print("{} {} {} {} {}".format(job.user, job.jobid,
                        #      overlap.seconds, job.cputimeraw, job.elapsedraw))
                        cputimeraw += (job.cputimeraw * overlap.total_seconds() /
                                       job.elapsedraw)
                        gputimeraw += (job.gputimeraw * overlap.total_seconds() /
                                       job.elapsedraw)
            user = User(name=username, njobs=njob, cputimeraw=cputimeraw,
                        gputimeraw=gputimeraw)
            userL.append(user)

        # Sort by GPU usage
        userbygpuL = sorted(userL, key=operator.attrgetter('gputimeraw'), reverse=True)
        userbycpuL = sorted(userL, key=operator.attrgetter('cputimeraw'), reverse=True)

        #### CPU
        usertimeL = [user.cputimeraw for user in userbycpuL]
        usernameL = [user.name for user in userbycpuL]
        totalsystemcputime = walltime * nnodes * ncpupernode
        colorD = make_pie(sortedtimeL = usertimeL, sortednameL = usernameL,
                          totalsystime=totalsystemcputime, title="CPU")

        #### GPU
        usertimeL = [user.gputimeraw for user in userbygpuL]
        usernameL = [user.name for user in userbygpuL]
        totalsystemgputime = walltime * nnodes * ngpupernode
        if engine == 'plotly':
            raise NotImplementedError("ERROR!! No plotly pie charts enabled yet")
        make_pie(sortedtimeL = usertimeL, sortednameL = usernameL,
                          colorD=colorD, totalsystime=totalsystemgputime, title="GPU")

    elif plottype == 'time-series':
        interval = 3600 * 24    # in seconds
        totaltimeperinterval = interval * nnodes * ngpupernode
        if users is None:
            raise ValueError("ERROR!! Please specify which users to plot")
        if engine == 'matplotlib':
            plot_time_series_mpl(jobL=jobL, start=mintime, end=maxtime,
                             interval=interval, cpuorgpu='gpu',
                             totalsystime=totaltimeperinterval, users=users,
                             totalutil1d = totalutil1d)
        elif engine == 'plotly' :
            plot_time_series_plotly(jobL=jobL, start=mintime, end=maxtime,
                             interval=interval, cpuorgpu='gpu',
                             totalsystime=totaltimeperinterval, users=users)
        else:
            raise ValueError("ERROR!! Invalid value ({}) for 'engine'".format(engine))

    ## Extract by time range
    sys.stdout.flush()
    sys.exit(0)


if __name__ == "__main__":

    main()


