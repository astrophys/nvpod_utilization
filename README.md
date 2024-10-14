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


## References
1. [Baseview Admin Manual](https://support.brightcomputing.com/manuals/10/admin-manual.pdf)
