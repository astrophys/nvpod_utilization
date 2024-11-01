# Author : Ali Snedden
# Date   : 10/31/24
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
import datetime
import matplotlib
import numpy as np
import pandas as pd
matplotlib.use('tkagg')
from typing import List,Dict
import matplotlib.pyplot as plt
from functions import make_autopct
from numpy.typing import ArrayLike
from classes import Job,Step,SacctObj,User
from functions import is_job_in_time_range


def make_pie(sortedtimeL : List[float] = None, sortednameL : List[str] = None,
             totalsystime : float = None, colorD : Dict[str, str] = None,
             title : str = None):
    """Generates pie plot

    Args

        N/A

    Returns

    Raises

    """
    fig = plt.figure()
    gs = fig.add_gridspec(1,1)
    # cpu
    ax = fig.add_subplot(gs[0,0])

    # Get unused time
    unusedtime = totalsystime - sum(sortedtimeL)
    usertimeV = np.asarray(sortedtimeL)
    usertimeV = usertimeV / 3600
    usernameL = sortednameL
    # Split users based off of usage
    totalcputime = np.sum(usertimeV)
    #### # https://matplotlib.org/stable/gallery/pie_and_polar_charts/bar_of_pie.html#sphx-glr-gallery-pie-and-polar-charts-bar-of-pie-py
    percentusertimeV = usertimeV / np.sum(usertimeV) * 100
    usernameV = np.asarray(usernameL)
    namethresh = 1
    if colorD is None:
        wedges, *_ = ax.pie(usertimeV / np.sum(usertimeV),
                            autopct=make_autopct(percentusertimeV, usernameV,
                                                 namethresh))
    else :
        colorL = []
        for user in usernameL:
            colorL.append(colorD[user])
        wedges, *_ = ax.pie(usertimeV / np.sum(usertimeV), colors=colorL,
                            autopct=make_autopct(percentusertimeV, usernameV,
                                                 namethresh))
    usernamepercentL = []
    for i in range(len(usernameL)):
        user = usernameL[i]
        usernamepercentL.append("{:.2f}% : {} ".format(percentusertimeV[i], user,
                                namethresh))
    fig.legend(wedges, usernamepercentL, loc="right")
    ax.set_title("{} : {:.1f}% allocated".format(title, (1-unusedtime/totalsystime)*100))
    ## Extract by time range
    fig.show()

    print("{} Allocated ({:.1f}) by user out of total cpu time {}h "
          "available ".format(title,(1-unusedtime/totalsystime)*100,
                              totalsystime/3600))
    for i in range(len(usertimeV)):
        print("\t{:<10} : {:<10.2f}h = {:<2.2f}%".format(usernameL[i],
              usertimeV[i], percentusertimeV[i]))

    ### Keep user color consistent across graphs
    colorD = dict()
    for i in range(len(wedges)):
        colorD[usernameL[i]] = wedges[i]._original_facecolor
    return colorD


def make_time_series(jobL : List[Job] = None, start : datetime.datetime = None,
                     end : datetime.datetime = None, interval : float = None,
                     cpuorgpu : str = None, totalsystime : float = None):
    """Generates time series plot. Integrate over interval between 'start' and 'end'

    Args

        N/A

    Returns

    Raises

    """
    delta = datetime.timedelta(seconds=interval)
    date = start
    usageL = []
    timeL = []
    # Loop over intervals
    while date <= end:
        #print(date.strftime("%Y-%m-%d"))
        # Time interval
        mint = date
        maxt = date + delta
        print("{}   --->   {}".format(mint.strftime("%Y-%m-%d"),
              maxt.strftime("%Y-%m-%d")))
        timeraw = 0
        for job in jobL:
            inrange, overlap = is_job_in_time_range(job, mint, maxt)
            if inrange == True:
                if cpuorgpu.lower() == 'gpu':
                    if job.elapsedraw > 0:
                        timeraw += (job.gputimeraw * overlap.total_seconds() /
                                    job.elapsedraw)
                elif cpuorgpu.lower() == 'cpu':
                    if job.elapsedraw > 0:
                        timeraw += (job.cputimeraw * overlap.total_seconds() /
                                   job.elapsedraw)
                else:
                    raise ValueError("ERROR!!! Invalid value for cpuorgpu"
                                     " {}".format(cpuorgpu))
        usageL.append(timeraw)
        timeL.append(date + delta/2.0)
        print("{} : {}".format(timeL[-1], timeraw / totalsystime * 100))
        date += delta
    usageV = np.asarray(usageL)

    #### Plot
    fig = plt.figure()
    gs = fig.add_gridspec(1,1)
    # cpu
    ax = fig.add_subplot(gs[0,0])
    ax.plot(timeL,usageV/ totalsystime * 100)
    #https://stackoverflow.com/a/56139690/4021436
    #ax.set_xticklabels(timeL, rotation=45, ha='right')
    ax.tick_params(axis='x', labelrotation=45)
    ax.set_title("Percent {} allocation ".format(cpuorgpu))
    ax.set_ylabel("{} % allocation".format(cpuorgpu))
    print("Time Sum = {}".format(np.sum(usageV)))
    print("Total Time avail = {}".format(totalsystime))
    print("Average Utilization = {}".format(np.mean(usageV)/totalsystime))

    ## Extract by time range
    fig.show()
