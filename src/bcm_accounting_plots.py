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
#import itertools
import operator
import matplotlib
import numpy as np
import pandas as pd
#matplotlib.use('tkagg')        # Linux
matplotlib.use('qtagg')        # Linux
from classes import User
from functools import reduce
import matplotlib.pyplot as plt
from plot_funcs import make_pie
from functions import make_autopct
from functions import parse_sacct_file
from functions import is_job_in_time_range
from plot_funcs import plot_time_series_mpl
from plot_funcs import plot_time_series_plotly


# Expects data like : sacct --allusers -P -S 2024-08-01 --format="jobidraw,jobname,user,nodelist,elapsedraw,alloccpus,cputimeraw,maxrss,state,start,end,reqtres" > sacct_2024-08-01.txt

# Run via
#    python -m pdb src/bcm_accounting_plots.py --path data/sacct_2024-05-01_to_2024-10-31.txt --start 2024-05-01T00:00:00 --end 2024-11-01T00:00:00 --plottyp time-series --users all
#   python -m pdb src/bcm_accounting_plots.py --path data/20250214/sacct_2025-02-14_short --start 2025-01-31T00:00:00 --end 2025-02-13T00:00:00 --plot_type time-series --users total_alloc+util --engine matplotlib --totalutil_1d data/20250214/totalgpuutilization_1d.txt --exclude_nodes rceabrg01,rceabrg02 --plot_title "GPU allococation and utilization excluding rceabrg[01-02]"
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
    parser.add_argument('--plot_type', metavar='plottype', type=str,
                        help='Options : "histogram", "pie" or "time-series"')
    parser.add_argument('--users', metavar='users', type=str,
                        help='Options : "all", "total", "total_alloc+util", or '
                        '"someuser"')
    parser.add_argument('--engine', metavar='engine', type=str,
                        help='Options : "plotly" or "matplotlib" (default)')
    parser.add_argument('--totalutil', metavar='path/to/gpuutilization_[1h,1d]',
                        type=str, help='Total utilization file, e.g. 1h or 1d')
    parser.add_argument('--exclude_nodes', metavar='exclude_nodes', nargs='?',
                        type=str, help='Exclude nodes from calculation. Useful when'
                                       'considering nodes that have MIGs enabled')
    parser.add_argument('--plot_title', metavar='plottitle', nargs='?',
                        type=str, help='Set title of plot')
    parser.add_argument('--hourinterval', metavar='hourinterval', nargs='?',
                        help='Time interval in h, only valid for time-series',
                        type=str )
    args = parser.parse_args()
    path = args.path
    users = args.users
    plottype = args.plot_type
    ###
    if args.hourinterval is not None :
        hourinterval = float(args.hourinterval)
    else :
        hourinterval = 24
    ###
    if ((args.totalutil).split('_')[-1]).split('.')[0] == '1d' :
        totalutil = args.totalutil
        if hourinterval < 24 :
            raise ValueError("ERROR!!! Can't have time resolution less than 1d "
                             "when using a 1d utilization file")
    elif ((args.totalutil).split('_')[-1]).split('.')[0] == '1h' :
        totalutil = args.totalutil
    elif args.totalutil is not None:
        raise ValueError("ERROR!!! Please use a total utilization file with "
                         "either a '_1h.txt' or '_1d.txt' suffix")
    engine = args.engine
    title = args.plot_title
    if args.exclude_nodes is not None :
        if('[' in args.exclude_nodes or ']' in args.exclude_nodes or
           '-' in args.exclude_nodes):
            raise ValueError("ERROR!!! You must write the full name of each node")
        excludenodeL = args.exclude_nodes.split(',')
    else :
        excludenodeL = None
    if engine is None :
        engine = 'matplotlib'
    mintime = datetime.datetime.strptime(args.start, "%Y-%m-%dT%H:%M:%S")
    maxtime = datetime.datetime.strptime(args.end, "%Y-%m-%dT%H:%M:%S")
    if maxtime < mintime :
        raise ValueError("ERROR!!! mintime ({}) > maxtime "
                         "({})".format(mintime,maxtime))
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

    # Exclude nodes...
    if excludenodeL is not None :
        idx=0
        subsetL = []
        includednodeL = []
        for job in jobL :
            keep = True
            for node in excludenodeL :
                if node in job.nodelist :
                    keep = False
                    break
            if keep is True :
                idx += 1
                subsetL.append(job)
                # Handle lists of differing length
                if len(job.nodelist) == 1 :
                    includednodeL.append(job.nodelist[0])
                elif len(job.nodelist) > 1 :
                    includednodeL.extend(job.nodelist)
                else :
                    raise ValueError("ERROR!! Invalid job.nodelist "
                                     "{}".format(job.nodelist))
        #includednodeL = list(itertools.chain.from_iterable(includednodeL))
        print("Included Nodes : ")
        for node in sorted(set(includednodeL)):
            print("\t{}".format(node))
        print("Excluded Nodes : ")
        for node in excludenodeL:
            print("\t{}".format(node))
        print("Originally had {} jobs".format(len(jobL)))
        print("Now have {} jobs\n".format(len(subsetL)))
        jobL = subsetL
        nnodes = nnodes - len(excludenodeL)

    ### Diagnostics, ensure we rm'd excluded notes
    # tmpL=[]
    # for job in jobL:
    #     if len(job.nodelist) == 1 :
    #         tmpL.append(job.nodelist[0])
    #     elif len(job.nodelist) > 1 :
    #         tmpL.extend(job.nodelist)
    # print("jobL only uses nodes: ")
    # for node in sorted(set(tmpL)):
    #     print("\t{}".format(node))

    print("nnodes = {}".format(nnodes))
    print("ngpupernode = {}".format(ngpupernode))
    print("ncpupernode = {}".format(ncpupernode))


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
        interval = 3600 * hourinterval # in seconds
        totaltimeperinterval = interval * nnodes * ngpupernode
        print("hourinterval = {}h".format(hourinterval))
        print("interval size = {}s".format(interval))
        print("totaltimeperinterval = {}s".format(totaltimeperinterval))
        if users is None:
            raise ValueError("ERROR!! Please specify which users to plot")
        if engine == 'matplotlib':
            plot_time_series_mpl(jobL=jobL, start=mintime, end=maxtime,
                             interval=interval, cpuorgpu='gpu',
                             totalsystime=totaltimeperinterval, users=users,
                             totalutil = totalutil, title=title)
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


