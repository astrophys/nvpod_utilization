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
matplotlib.use('tkagg')
from classes import User
from collections import Counter
import matplotlib.pyplot as plt
from functions import make_autopct
from functions import parse_sacct_file
from functions import is_job_in_time_range
from functions import group_users_by_usage
from matplotlib.patches import ConnectionPatch
from sklearn.feature_extraction.text import CountVectorizer


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
    parser.add_argument('--path', metavar='path/to/sacct_text_file', type=str,
                        help='Path to parsable sacct file')
    parser.add_argument('--start', metavar='starttime', type=str,
                        help='Time in YYYY-MM-DDTHH:MM:SS format')
    parser.add_argument('--end', metavar='endtime', type=str,
                        help='Time in YYYY-MM-DDTHH:MM:SS format')
    parser.add_argument('--plottype', metavar='plottype', type=str,
                        help='Options : "histogram", "pie" or "time-series"')
    #parser.add_argument('--plottype', metavar='plottype', type=str,
    #                    help='Options : "histogram", "pie" or "time-series"')
    args = parser.parse_args()
    path = args.path
    plottype = args.plottype
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
    (jobL,starttime,endtime) = parse_sacct_file(path=path)

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
                    #print("{} {} {} {} {}".format(job.user, job.jobid, overlap.seconds,
                    #      job.cputimeraw, job.elapsedraw))
                    cputimeraw += job.cputimeraw * overlap.total_seconds() / job.elapsedraw
                    gputimeraw += job.gputimeraw * overlap.total_seconds() / job.elapsedraw
        user = User(name=username, njobs=njob, cputimeraw=cputimeraw,
                    gputimeraw=gputimeraw)
        userL.append(user)

    # Sort by GPU usage
    userbygpuL = sorted(userL, key=operator.attrgetter('gputimeraw'), reverse=True)
    userbycpuL = sorted(userL, key=operator.attrgetter('cputimeraw'), reverse=True)

    # total time avail
    totalsystemcputime = walltime * nnodes * ncpupernode
    totalsystemgputime = walltime * nnodes * ngpupernode

    if plottype == 'pie':
        fig = plt.figure()
        gs = fig.add_gridspec(1,1)
        # cpu
        ax = fig.add_subplot(gs[0,0])
        usertimeL = [user.cputimeraw for user in userbycpuL]
        usernameL = [user.name for user in userbycpuL]
        # Get unused time
        unusedtime = totalsystemcputime - sum(usertimeL)
        usertimeV = np.asarray(usertimeL)
        usertimeV = usertimeV / 3600
        # Split users based off of usage
        totalcputime = np.sum(usertimeV)
        #### # https://matplotlib.org/stable/gallery/pie_and_polar_charts/bar_of_pie.html#sphx-glr-gallery-pie-and-polar-charts-bar-of-pie-py
        percentusertimeV = usertimeV / np.sum(usertimeV) * 100
        usernameV = np.asarray(usernameL)
        namethresh = 1
        wedges, *_ = ax.pie(usertimeV / np.sum(usertimeV), autopct=make_autopct(percentusertimeV,usernameV,namethresh))
        usernamepercentL = []
        for i in range(len(usernameL)):
            user = usernameL[i]
            usernamepercentL.append("{:.2f}% : {} ".format(percentusertimeV[i], user, namethresh))
        fig.legend(wedges, usernamepercentL, loc="right")
        ax.set_title("CPU : {:.1f}% used".format((1-unusedtime/totalsystemcputime)*100))
        ## Extract by time range
        fig.show()

        print("CPU Usage ({:.1f}) by user out of total cpu time {}h "
              "available ".format((1-unusedtime/totalsystemcputime)*100, totalsystemcputime/3600))
        for i in range(len(usertimeV)):
            print("\t{:<10} : {:<10.2f}h = {:<2.2f}%".format(usernameL[i],
                  usertimeV[i], percentusertimeV[i]))

        ### Keep user color consistent across graphs
        colorD = dict()
        for i in range(len(wedges)):
            colorD[usernameL[i]] = wedges[i]._original_facecolor

        # Re-enable later, after debugging
        # gpu
        fig = plt.figure()
        gs = fig.add_gridspec(1,1)
        # cpu
        ax = fig.add_subplot(gs[0,0])
        #ax = fig.add_subplot(gs[1,0])
        usertimeL = [user.gputimeraw for user in userbygpuL]
        usernameL = [user.name for user in userbygpuL]
        usernameV = np.asarray(usernameL)
        # Ensure identical colors across plots
        colorL = []
        for user in usernameL:
            colorL.append(colorD[user])
        # Get unused time
        unusedtime = totalsystemgputime - sum(usertimeL)
        usertimeV = np.asarray(usertimeL)
        usertimeV = usertimeV / 3600
        percentusertimeV = usertimeV / np.sum(usertimeV) * 100
        wedges, *_ = ax.pie(usertimeV / np.sum(usertimeV), colors=colorL, autopct=make_autopct(percentusertimeV,usernameV,namethresh))
        ax.set_title("GPU : {:.1f}% used".format((1-unusedtime/totalsystemgputime)*100))
        usernamepercentL = []
        for i in range(len(usernameV)):
            user = usernameV[i]
            usernamepercentL.append("{:.2f}% : {} ".format(percentusertimeV[i], user, namethresh))
        fig.legend(wedges, usernamepercentL, loc="right")
        print("GPU Usage ({:.1f}) by user out of total gpu time {}h "
              "available ".format((1-unusedtime/totalsystemgputime)*100, totalsystemgputime/3600))
        for i in range(len(usertimeV)):
            print("\t{:<10} : {:<10.2f}h = {:<2.2f}%".format(usernameL[i], usertimeV[i], percentusertimeV[i]))


    ## Extract by time range
    fig.show()

    sys.stdout.flush()
    sys.exit(0)


if __name__ == "__main__":

    main()


