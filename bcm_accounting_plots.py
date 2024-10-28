# Author : Ali Snedden
# Date   : 09/18/24
# License:
#
#
# Goals (ranked by priority) :
#
# Refs :
#   a)
#   #) https://www.nltk.org/book/ch06.html
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
from functions import parse_sacct_file
from functions import is_job_in_time_range
from functions import group_users_by_usage
from matplotlib.patches import ConnectionPatch
from sklearn.feature_extraction.text import CountVectorizer


# Expects data like : sacct --allusers -P -S 2024-08-01 --format="jobid,user,partition,alloccpus,elapsed,cputime,state,tres" > sacct_2024-08-01.txt

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
    totalcputime = walltime * nnodes * ncpupernode
    totalgputime = walltime * nnodes * ngpupernode

    if plottype == 'pie':
        fig = plt.figure()
        gs = fig.add_gridspec(1,4)
        # cpu
        ax = fig.add_subplot(gs[0,0])
        usertimeL = [user.cputimeraw for user in userbycpuL]
        usernameL = [user.name for user in userbycpuL]
        # Get unused time
        unusedtime = totalcputime - sum(usertimeL)
        ### usertimeL.append(unusedtime)
        ### usernameL.append("unused")
        usertimeV = np.asarray(usertimeL)
        usertimeV = usertimeV / 3600
        # Split users based off of usage
        topuserL,toptimeV,lowuserL,lowtimeV = group_users_by_usage(usernameL,
                                                                   usertimeV,
                                                                   thresh=0.03)
        topuserL.append('')
        toptimeV = np.append(toptimeV, np.sum(lowtimeV))
        # https://matplotlib.org/stable/gallery/pie_and_polar_charts/bar_of_pie.html#sphx-glr-gallery-pie-and-polar-charts-bar-of-pie-py
        # rotate so that first wedge is split by the x-axis
        #startangle = -180 * toptimeV[0]
        wedges, *_ = ax.pie(toptimeV, labels=topuserL, autopct='%1.1f%%')
        ### Do expanded bar
        bottom = 1
        width  = 0.2
        ax.set_title("CPU : {:.1f}% used".format((1-unusedtime/totalcputime)*100))
        ax2 = fig.add_subplot(gs[0,1])
        n = len(lowtimeV)
        for j, (height, label) in enumerate(reversed([*zip(lowtimeV/np.sum(lowtimeV), lowuserL)])):
            bottom -= height
            bc = ax2.bar(0, height, width, bottom=bottom, color='C0', label=label,
                         alpha=1/n * j)
            ax2.bar_label(bc, labels=[f"{height:.0%}"], label_type='center')

        ax2.set_title('CPU usage')
        ax2.legend()
        ax2.axis('off')
        ax2.set_xlim(- 2.5 * width, 2.5 * width)

        # use ConnectionPatch to draw lines between the two plots
        theta1, theta2 = wedges[-1].theta1, wedges[-1].theta2
        center, r = wedges[-1].center, wedges[-1].r
        bar_height = sum(lowtimeV)

        # draw top connecting line
        x = r * np.cos(np.pi / 180 * theta2) + center[0]
        y = r * np.sin(np.pi / 180 * theta2) + center[1]
        #x = r * np.cos(theta2) + center[0]
        #y = r * np.sin(theta2) + center[1]
        con = ConnectionPatch(xyA=(-width / 2, bar_height), coordsA=ax2.transData,
                              xyB=(x, y), coordsB=ax.transData)
        con.set_color([0, 0, 0])
        con.set_linewidth(4)
        ax2.add_artist(con)

        ## # draw bottom connecting line
        ## #x = r * np.cos(np.pi / 180 * theta1) + center[0]
        ## #y = r * np.sin(np.pi / 180 * theta1) + center[1]
        ## x = r * np.cos(theta1) + center[0]
        ## y = r * np.sin(theta1) + center[1]
        ## con = ConnectionPatch(xyA=(-width / 2, 0), coordsA=ax2.transData,
        ##                       xyB=(x, y), coordsB=ax.transData)
        ## con.set_color([0, 0, 0])
        ## ax2.add_artist(con)
        ## con.set_linewidth(4)





        print("CPU Usage by user out of total cpu time {}h available ".format(totalcputime/3600))
        for i in range(len(usertimeV)):
            print("\t{:<10} : {:<15.2f}h".format(usernameL[i], usertimeV[i]))




        # gpu
        ax = fig.add_subplot(gs[0,2])
        usertimeL = [user.gputimeraw for user in userbygpuL]
        usernameL = [user.name for user in userbygpuL]
        # Get unused time
        unusedtime = totalgputime - sum(usertimeL)
        ### usertimeL.append(unusedtime)
        ### usernameL.append("unused")
        usertimeV = np.asarray(usertimeL)
        usertimeV = usertimeV / 3600
        ax.pie(usertimeV, labels=usernameL, autopct='%1.1f%%')
        ax.set_title("GPU : {:.1f}% used".format((1-unusedtime/totalgputime)*100))
        print("GPU Usage by user out of total gpu time {}h available ".format(totalgputime/3600))
        for i in range(len(usertimeV)):
            print("\t{:<10} : {:<15.2f}h".format(usernameL[i], usertimeV[i]))


    ## Extract by time range
    fig.show()

    sys.stdout.flush()
    sys.exit(0)


if __name__ == "__main__":

    main()


