import os
import sys
import random
import datetime
import numpy as np
from numpy.typing import ArrayLike
import pandas as pd
from typing import List
from classes import Job,Step,SacctObj,User

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
    df = pd.read_csv(path, sep='|', na_filter=False)
    ## group by jobid, strip off '.ext', '.batch' and step number appende by sact
    #jobnum = df['JobID'].str.split('.', expand=True)[0]
    #df['jobnum'] = jobnum
    ## Get unique job numbers
    jobL = []
    uniqjobnumV = np.unique(df['JobID'].str.split('.', expand=True)[0])
    endtime   = datetime.datetime.strptime(df['End'].iloc[0], "%Y-%m-%dT%H:%M:%S")
    starttime = datetime.datetime.strptime(df['Start'].iloc[0], "%Y-%m-%dT%H:%M:%S")

    for jobid in uniqjobnumV:
        jobdf = df[df['JobID'].str.contains(jobid)]
        #### get toplevel job...
        job = jobdf[~jobdf['JobID'].str.contains('\.')]       # top level job does not contain
        jobname = job['JobName'].values[0]
        user    = job['User'].values[0]
        nodelist= job['NodeList'].values[0]
        elapsedraw = job['ElapsedRaw'].values[0]
        alloccpus  = job['AllocCPUS'].values[0]
        cputimeraw = job['CPUTimeRAW'].values[0]
        maxrss     = job['MaxRSS'].values[0]
        state      = job['State'].values[0]
        start      = job['Start'].values[0]
        end        = job['End'].values[0]
        reqtres    = job['ReqTRES'].values[0]
        #
        jobobj = Job(jobid=jobid, jobname=jobname, user=user, nodelist=nodelist,
                     elapsedraw=elapsedraw, alloccpus=alloccpus,
                     cputimeraw=cputimeraw, state=state,
                     start=start, end=end, reqtres=reqtres)
        ### Get job steps, batch/bash, extern
        for line in jobdf[jobdf['JobID'].str.contains('\.')].iterrows() :
            #job = # top level job does not contain
            #line.jobid
            jobname = line[1]['JobName']
            user    = line[1]['User']
            nodelist= line[1]['NodeList']
            elapsedraw = line[1]['ElapsedRaw']
            alloccpus  = line[1]['AllocCPUS']
            cputimeraw = line[1]['CPUTimeRAW']
            maxrss     = line[1]['MaxRSS']
            state      = line[1]['State']
            start      = line[1]['Start']
            end        = line[1]['End']
            reqtres    = line[1]['ReqTRES']
            #jobid = jobid
            sacctobj = SacctObj(jobid=jobid, jobname=jobname, nodelist=nodelist,
                         elapsedraw=elapsedraw, alloccpus=alloccpus,
                         cputimeraw=cputimeraw, state=state,
                         start=start, end=end)
            if 'batch' in line[1]['JobID']:
                jobobj.batchL.append(sacctobj)
            elif 'extern' in line[1]['JobID']:
                jobobj.externL.append(sacctobj)
            # Everything else must be a 'step', might screw me later.
            else:
                jobobj.stepL.append(sacctobj)
        jobL.append(jobobj)


        if jobobj.state != 'RUNNING' and endtime < jobobj.end:
            endtime = jobobj.end
        if jobobj.start is not None and endtime < jobobj.start:
            endtime = jobobj.start

        if jobobj.start is not None and starttime > jobobj.start:
            starttime = jobobj.start
        if jobobj.state != 'RUNNING' and starttime > jobobj.end:
            raise ValueError("ERROR!!! Does this ever happen?")
            starttime = jobobj.end
    print("Earliest Time : {}".format(starttime))
    print("Latest Time   : {}".format(endtime))
    return(jobL,starttime,endtime)



def string2time(string : str = None):
    """Takes string in format YYYY-MM-DDTHH:MM:SS to a Python time

    Args
        string : time in format YYYY-MM-DDTHH:MM:SS

    Returns

    Raises

    """
    return datetime.datetime.strptime(string, "%Y-%m-%dT%H:%M:%S")


def is_job_in_time_range(job : Job = None, mintime : datetime.datetime = None,
                         maxtime : datetime.datetime = None):
    """Returns True or False if the job.start / job.end fall within the time range

    Args
        job  =  Job of interest
        mintime = datetime object passed via CL
        maxtime = datetime object passed via CL

    Returns
        bool in range

    Raises

    """
    # I don't know how to handle jobs with an invalid start time
    if job.start is None:
        print("Job {} has invalid start time {}...."
              "skipping".format(job.jobid,job.start))
        inrange=False
        overlap=0
        return inrange,overlap
    if job.end is None:
        print("Job {} has invalid end time {}, in state {}...."
              "skipping".format(job.jobid, job.end, job.state))
        inrange=False
        overlap=0
        return inrange,overlap
    if(job.start < mintime and job.end < mintime):
        #  timerange :                     mintime    maxtime
        #                                    |-----------|
        #  job       :     |------------|
        #               job.start    job.end
        inrange = False
        overlap = 0

    elif(job.start > maxtime and job.end > maxtime):
        #  timerange : mintime    maxtime
        #                |-----------|
        #  job       :                   |--------------|
        #                             job.start      job.end
        inrange = False
        overlap = 0

    elif(mintime <= job.end and job.end <= maxtime and
         job.start <= mintime and job.start <= maxtime):
        #  timerange :          mintime          maxtime
        #                          |---------------|
        #  job       :    |----------------|
        #             job.start         job.end
        inrange = True
        overlap = job.end - mintime

    elif(mintime <= job.start and job.start <= maxtime and
         job.end >= mintime and job.end >= maxtime):
        #  timerange :    mintime          maxtime
        #                    |---------------|
        #  job       :               |----------------|
        #                        job.start         job.end
        inrange = True
        overlap = maxtime - job.start

    elif(job.start <= mintime and job.start <= maxtime and
         job.end >= mintime and job.end >= maxtime):
        #  timerange :              mintime          maxtime
        #                             |-----------------|
        #  job       :          |-------------------------------|
        #                    job.start                        job.end
        inrange = True
        overlap = maxtime - mintime

    elif(mintime <= job.start and job.start <= maxtime and
         mintime <= job.end   and job.end <= maxtime):
        #  timerange :  mintime                         maxtime
        #                 |--------------------------------|
        #  job       :          |-----------------|
        #                    job.start         job.end
        inrange = True
        overlap = job.end - job.start
    else:
        raise ValueError("Error!!! Unhandled condition")

    # inrange,overlap
    return inrange,overlap


def group_users_by_usage(userL : List[str] = None, timeV : ArrayLike = None,
                         thresh : float = None):
    """Take a list of users and user cpu/gpu times and group s.t. you can plot
       low usage users in an expanded bar plot in pie chart

    Args
        userL   = sorted list of users names matching timeL
        timeL   = sorted list of times (any units) matching userL
        thresh  = float from [0,1] fraction of full pie to put in the expanded
                  bar

    Returns
        topuserL  = users to keep in pie chart
        toptimeL  = users' time to keep in pie chart
        lowtimeL  = users to put in expanded bar view
        lowuserL  = users' time to put in expanded bar view

    Raises
    """
    if timeV[-1] > timeV[0]:
        raise ValueError("ERROR!!! Doesn't seem  like timeV is sorted by "
                         "decreasing values")
    if len(userL) != timeV.shape[0]:
        raise ValueError("ERROR!!! len(userL) != timeV.shape[0] ")
    total = np.sum(timeV)
    for i in range(1,len(userL)):
        subtot = np.sum(timeV[-i:])
        percent = subtot / total
        if percent > thresh:
            break
    topuserL = userL[:1-i]
    toptimeV = timeV[:1-i]
    lowtimeV = timeV[1-i:]
    lowuserL = userL[1-i:]

    if not np.isclose((np.sum(toptimeV) + np.sum(lowtimeV))/total, 1):
        raise ValueError("ERROR!!! (np.sum(toptimeV) + np.sum(lowtimeV))/total != 1")

    return (topuserL,toptimeV,lowuserL,lowtimeV)

