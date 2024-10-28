# NVPOD utilization
#### Author : Ali Snedden
#### LICENSE : GPL-3

## Abstract
While running a Nvidia Super/Base-POD, one would like to accumulate relevant plots / statistics to present to management and customers. 
These include job / node level cpu / gpu utilization. 
I'm fairly familiar with how to interact with the slurm accounting database and I'd like to learn how to use the Base View measurables database


## Background
1. Per Section 12.4 of Admin manual, the telemetry data collected by BCM is dropped 
after a period of time. This makes historical lookback challenging.
2 Looking at `man sacct`, under TotalCPU it says processes interrupted may not have accurate information.


## Dependencies
1. Slurm
2. Base Command Manager (v10.0) with associated Nvidia hardware
3. You might need to install python3-tk in Ubuntu

## Job States
You may come across a variety of job states that may be challenging to understand.
Refer to `man sacct` to understand the meaning of the fields described below. 

Gotchya's:
1. A `RUNNING` job won't have an End time.
2. Some jobs that didn't run for one second (e.g. failed immediately) will have an elapsed time = 0s.


## References
1. [Baseview Admin Manual](https://support.brightcomputing.com/manuals/10/admin-manual.pdf)
