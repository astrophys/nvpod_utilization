# Author : Ali Snedden
# Date   : 10/31/24
# Goals (ranked by priority) :
#
# Refs :
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
import plotly.express as px
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from functions import make_autopct
from numpy.typing import ArrayLike
from collections import OrderedDict
from plotly.subplots import make_subplots
from classes import Job,Step,SacctObj,User,TotalGpu
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


def gather_time_series(jobL : List[Job] = None, start : datetime.datetime = None,
                     end : datetime.datetime = None, interval : float = None,
                     cpuorgpu : str = None, totalsystime : float = None):
    """Gathers data for time series plot.

    Args

        N/A

    Returns

    Raises

    """
    delta = datetime.timedelta(seconds=interval)
    date = start
    dateD = OrderedDict()

    # Loop over intervals
    while date <= end:
        # Time interval
        mint = date
        maxt = date + delta
        midt = date + delta/2.0
        userD = dict()
        print("{}   --->   {}".format(mint.strftime("%Y-%m-%d"),
              maxt.strftime("%Y-%m-%d")))
        totalraw = 0
        for job in jobL:
            inrange, overlap = is_job_in_time_range(job, mint, maxt)
            if inrange == True:
                if cpuorgpu.lower() == 'gpu':
                    if job.elapsedraw > 0:
                        jobraw  = (job.gputimeraw * overlap.total_seconds() /
                                   job.elapsedraw)
                        totalraw += jobraw
                elif cpuorgpu.lower() == 'cpu':
                    if job.elapsedraw > 0:
                        jobraw    = (job.cputimeraw * overlap.total_seconds() /
                                     job.elapsedraw)
                        totalraw += jobraw
                else:
                    raise ValueError("ERROR!!! Invalid value for cpuorgpu"
                                     " {}".format(cpuorgpu))
                ### Add to userD dictionary
                if job.user in userD.keys():
                    userD[job.user] += jobraw
                else :
                    userD[job.user] = jobraw
        userD['total'] = totalraw
        dateD[midt] = userD
        date += delta
    df = pd.DataFrame.from_dict(dateD, orient='index')
    df.sort_index(inplace=True)
    df.fillna(0, inplace=True)
    return df


def gather_totalgpu_time_series(totalgpu : TotalGpu = None,
                     start : datetime.datetime = None,
                     end : datetime.datetime = None, interval : float = None):
    """Gathers data for time series plot.

    Args

        N/A

    Returns

    Raises

    """
    delta = datetime.timedelta(seconds=interval)
    date = start
    dateD = OrderedDict()
    utilL = []

    print("{}   --->   {}".format(start.strftime("%Y-%m-%d"),
          end.strftime("%Y-%m-%d")))

    for util in totalgpu.totalgpu.utilL:
        if start <= util.time and util.time <= end:
            inrange = True
            dateD[util.time] = util.util
            print("{} {}".format(util.time, util.util))
    df = pd.DataFrame.from_dict(dateD, orient='index')
    df.sort_index(inplace=True)
    df.fillna(0, inplace=True)
    df = df.rename(columns={0:'util'})
    return df


def plot_time_series_mpl(jobL : List[Job] = None, start : datetime.datetime = None,
                     end : datetime.datetime = None, interval : float = None,
                     cpuorgpu : str = None, totalsystime : float = None,
                     users : str = None, totalutil : str = None, title : str = None):
    """Generates time series plot. Integrate over interval between 'start' and 'end'

    Args

        N/A

    Returns

    Raises

    """
    df = gather_time_series(jobL=jobL, start=start, end=end,
                            interval=interval, cpuorgpu=cpuorgpu,
                            totalsystime=totalsystime)
    #### Plot
    fig = plt.figure()

    ## Only 1 plot - the total
    if users == 'total' or users == 'total_alloc+util' :
        gs = fig.add_gridspec(1,1)
        # cpu
        ax = fig.add_subplot(gs[0,0])

        ## Total allocation with total utilization
        if users == 'total_alloc+util':
            #print("Average Utilization / Efficiency = {}".format())
            if title is None :
                ax.set_title("{} allocation and utilization".format(cpuorgpu))
            else :
                ax.set_title(title)
            ax.set_ylabel("{} % ".format(cpuorgpu))
            totalgpu = TotalGpu(path=totalutil)
            dfutil = gather_totalgpu_time_series(totalgpu = totalgpu, start=start,
                                                 end=end, interval=interval)
            ax.plot(dfutil['util'].index, dfutil['util'], color = 'red', label='utilization')
            print("Average Utilization = {:<.2f} %".format(np.mean(dfutil['util'])))
        else:
            ax.set_title("Percent {} allocation ".format(cpuorgpu))
            ax.set_ylabel("{} % allocation".format(cpuorgpu))

        ax.plot(df['total'].index, df['total'] / totalsystime * 100, label='allocation')
        #https://stackoverflow.com/a/56139690/4021436
        #ax.set_xticklabels(timeL, rotation=45, ha='right')
        ax.tick_params(axis='x', labelrotation=45)
        ax.set_ylim(0,100)
        ax.legend()
        print("Average Allocation  = {:<.2f} "
              "%".format(np.mean(df['total'])/totalsystime * 100))
        print("Time Sum = {}".format(np.sum(df['total'])))
        print("Total Time avail = {}".format(totalsystime))
        plt.savefig("total_gpu_allocation.pdf")
    ## Total + users plot
    elif users == 'all':
        topusers = np.sum(df, axis=0).sort_values(ascending=False)
        print("df.shape = {}".format(df.shape))
        #for user in topusers :
        #    print("{} : {}% ".format(topusers/(df.shape[0] * totalsystime) * 100))
        topnames = topusers.index[0:9]
        gs = fig.add_gridspec(3,3)
        j = 0
        i = 0
        n = 0
        for username in topnames:
            j = n % 3
            i = np.floor(n/3).astype(int)
            print(i,j)
            ax = fig.add_subplot(gs[i,j])
            ax.plot(df[username].index, df[username] / totalsystime * 100)
            #https://stackoverflow.com/a/56139690/4021436
            #ax.set_xticklabels(timeL, rotation=45, ha='right')
            if i == 2:
                ax.tick_params(axis='x', labelrotation=45)
            else:
                ax.set_xticklabels([])
            if j != 0:
                ax.set_yticklabels([])
            else:
                ax.set_ylabel("{} % allocation".format(cpuorgpu))
            print("Time Sum = {}".format(np.sum(df['total'])))
            print("Total Time avail = {}".format(totalsystime))
            percentutil = np.mean(df[username])/totalsystime * 100
            print("{} Utilization = {}".format(username, percentutil))
            ax.set_title("{} : {:.1f}%".format(username,percentutil))
            ax.set_ylim(0,100)
            n += 1
        if title is None :
            fig.suptitle("Percent {} allocation of top 8 users".format(cpuorgpu))
        else :
            fig.suptitle(title)


    ### Individual users
    else:
        gs = fig.add_gridspec(1,1)
        # cpu
        ax = fig.add_subplot(gs[0,0])
        ax.plot(df[users].index, df[users] / totalsystime * 100)
        #https://stackoverflow.com/a/56139690/4021436
        #ax.set_xticklabels(timeL, rotation=45, ha='right')
        ax.tick_params(axis='x', labelrotation=45)
        ax.set_title("{} - Percent {} allocation".format(users,cpuorgpu))
        ax.set_ylabel("{} % allocation".format(cpuorgpu))
        print("{}".format(users))
        print("\tTime Sum = {}".format(np.sum(df[users])))
        print("\tTotal Time avail = {}".format(totalsystime))
        print("\tAverage Utilization = {}".format(np.mean(df[users])/totalsystime))


    ## Extract by time range
    fig.show()


def plot_time_series_plotly(jobL : List[Job] = None, start : datetime.datetime = None,
                     end : datetime.datetime = None, interval : float = None,
                     cpuorgpu : str = None, totalsystime : float = None,
                     users : str = None):
    """Generates time series plot. Integrate over interval between 'start' and 'end'

    Args

        N/A

    Returns

    Raises

    """
    df = gather_time_series(jobL=jobL, start=start, end=end,
                            interval=interval, cpuorgpu=cpuorgpu,
                            totalsystime=totalsystime)
    #### Plot
    #fig = plt.figure()

    ## Only 1 plot - the total
    if users == 'total':
        df['date'] = df.index
        df['totpercent'] = df['total'] / totalsystime * 100
        fig = px.line(df, x="date", y="totpercent",
                      labels={"date":"Date",
                              "totpercent":"Percent GPU Allocated"},
                      title="Percent GPU Allocated")
        fig.write_html("total_gpu_allocated.html")

    ## Total + users plot
    elif users == 'all':
        topusers = np.sum(df, axis=0).sort_values(ascending=False)
        print("df.shape = {}".format(df.shape))
        #for user in topusers :
        #    print("{} : {}% ".format(user, topusers/(df.shape[0] * totalsystime) * 100))
        topnames = topusers.index[0:9]
        #gs = fig.add_gridspec(3,3)
        j = 1
        i = 1
        n = 0
        fig = make_subplots(rows=3, cols=3, subplot_titles=topnames)
        for username in topnames:
            j = np.floor( n % 3).astype(int)
            j = j+1
            i = np.floor( n/3).astype(int)
            i = i+1
            print(i,j)
            #ax = fig.add_subplot(gs[i,j])
            fig.add_trace(
                go.Scatter(x=df[username].index, y=df[username] / totalsystime * 100,
                          name=username),
                row=i, col=j)
            print("Time Sum = {}".format(np.sum(df['total'])))
            print("Total Time avail = {}".format(totalsystime))
            percentutil = np.mean(df[username])/totalsystime * 100
            print("{} Utilization = {}".format(username, percentutil))
            n += 1
        fig.update_yaxes(range=[0, 100])
        fig.write_html("all_gpu_allocated.html")


    ### Individual users
    else:
        df['date'] = df.index
        df['totpercent'] = df['total'] / totalsystime * 100
        df['userpercent'] = df[users] / totalsystime * 100
        fig = px.line(df, x="date", y="userpercent",
                      labels={"date":"Date",
                              "userpercent":"Percent GPU Allocated"},
                      title="Percent GPU Allocated by {}".format(users))
        fig.write_html("{}_gpu_allocated.html".format(users))

    ## Extract by time range
    fig.show()
