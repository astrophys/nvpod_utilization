#!/bin/bash
 
 
for((i=1; i<10; i++)); do
    echo "${HOSTSTEM}g0${i}"
    for((g=0; g<8; g++)); do
        cmsh -c "device; dumpmonitoringdata -6d now gpu_utilization:gpu${g} -n ${HOSTSTEM}g0${i}" > ${HOSTSTEM}g0${i}_gpuutil_gpu${g}_2min.txt
        cmsh -c "device; dumpmonitoringdata --consolidationinterval 1h -365d now gpu_utilization:gpu${g} -n ${HOSTSTEM}g0${i}" > ${HOSTSTEM}g0${i}_gpuutil_gpu${g}_1h.txt
        cmsh -c "device; dumpmonitoringdata --consolidationinterval 1d -365d now gpu_utilization:gpu${g} -n ${HOSTSTEM}g0${i}" > ${HOSTSTEM}g0${i}_gpuutil_gpu${g}_1d.txt
    done;
done;
 
for((i=10; i<=31; i++)); do
    echo "${HOSTSTEM}g${i}"
    for((g=0; g<8; g++)); do
        cmsh -c "device; dumpmonitoringdata -6d now gpu_utilization:gpu${g} -n ${HOSTSTEM}g${i}" > ${HOSTSTEM}g${i}_gpuutil_gpu${g}_2min.txt
        cmsh -c "device; dumpmonitoringdata --consolidationinterval 1h -365d now gpu_utilization:gpu${g} -n ${HOSTSTEM}g${i}" > ${HOSTSTEM}g${i}_gpuutil_gpu${g}_1h.txt
        cmsh -c "device; dumpmonitoringdata --consolidationinterval 1d -365d now gpu_utilization:gpu${g} -n ${HOSTSTEM}g${i}" > ${HOSTSTEM}g${i}_gpuutil_gpu${g}_1d.txt
    done;
done;


cmsh -c "partition; dumpmonitoringdata -7d now totalgpuutilization" > totalgpuutilization_2min.txt
cmsh -c "partition; dumpmonitoringdata --consolidationinterval 1h -365d now totalgpuutilization" > totalgpuutilization_1h.txt
cmsh -c "partition; dumpmonitoringdata --consolidationinterval 1d -365d now totalgpuutilization" > totalgpuutilization_1d.txt

sacct --allusers -P -S 2024-01-01 --format="jobidraw,jobname,user,nodelist,elapsedraw,alloccpus,cputimeraw,maxrss,state,start,end,reqtres" > sacct_`date +'%Y-%m-%d'`
