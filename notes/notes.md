07-october-2024
==================================
1. Let's compare BCM's chargeback vs. slurm accounting
    a) In bcm10-h01, as user jess, submitted job 327
        #. Sleeps for 180s
        #. `sacct`   
            ```
            $ sacct -j 327 --format="jobid,jobname,cputime,alloccpus,elapsed,state,maxrss"
            JobID           JobName    CPUTime  AllocCPUS    Elapsed      State     MaxRSS
            ------------ ---------- ---------- ---------- ---------- ---------- ----------
            327                wrap   00:03:00          1   00:03:00  COMPLETED
            327.batch         batch   00:03:00          1   00:03:00  COMPLETED        36K
            327.extern       extern   00:03:00          1   00:03:00  COMPLETED        92K
            ```

        #. BCM chargeback
            ```
            "User","Accounting info","Jobs","Runtime (s)","CPU (s)","CPU ($)","GPU (s)","Memory","Price ($)"
            "root","","1","55414","55414","5.5414","55414","152388500000000","33.248400000000004"
            "ali","","6","77848","77848","7.784800000000001","77848","214082000000000","46.7088"
            "eli","","29","197498","222340","22.234","197498","611435000000000","120.983"
            "jess","","1","180","180","0.018000000000000002","180","495000000000","0.108"
            ```

    #) Ran a second job as jess, job 328
        #. sbatch --cpus-per-task=2 --wrap="sleep 180s"
            ```
            $ sacct -j 328 --format="jobid,jobname,cputime,alloccpus,elapsed,state,maxrss"
            JobID           JobName    CPUTime  AllocCPUS    Elapsed      State     MaxRSS
            ------------ ---------- ---------- ---------- ---------- ---------- ----------
            328                wrap   00:06:00          2   00:03:00  COMPLETED
            328.batch         batch   00:06:00          2   00:03:00  COMPLETED        36K
            328.extern       extern   00:06:00          2   00:03:00  COMPLETED        88K
            ```
        #. BCM CHargeback
            ```
            "User","Accounting info","Jobs","Runtime (s)","CPU (s)","CPU ($)","GPU (s)","Memory","Price ($)"
            "root","","1","55414","55414","5.5414","55414","152388500000000","33.248400000000004"
            "ali","","6","77848","77848","7.784800000000001","77848","214082000000000","46.7088"
            "eli","","29","197498","222340","22.234","197498","611435000000000","120.983"
            "jess","","2","360","540","0.054","360","1485000000000","0.23399999999999999"
            ```
        #. Conclusion
            * BCM : CPU (s)     == `sacct : cputime`
            * BCM : Runtime (s) == `sacct : elapsed`
    #) From meeting on 15-october-2024, we decided to use Slurm's accounting rather
       than BCM chargeback b/c as can be seen above it is reporting GPU usage on a 
       system without a GPU
        #. Observed that it struggles with GPUs across multiple nodes


08-october-2024
==================================
1. Both cmsh and slurm track job metrics
    a) cmsh uses Promethysis, slurm uses something else
    #) cmsh
        #. See metric collection settings :
            [bcm10-h01->monitoring->setup[JobSampler]->jobmetricsettings]% show
        #. Settings
            * Sampling Type :
                + `bright` : disables Prometheus samplin
                + `prometheus` : disables sampling by BCM metrics
                + `both` : enables both
            * Map jobs to GPUs
                + Associate the job with GPUs where the job processes run, where
                  possible (default: yes)
    #) When a job is started, BCM adds cm-cgroup-job-keepalive to job's cgroup
        #. Does no work, just prevents cgroup fom being deleted
        #. After job ends, WLM would remove the cgroup, but cm-cgroup-job-keepalive
           keeps the job open long enough to collect the last sample of the data
        #. Only lives for 8weeks
    #) Looking at `systemd-cgls`
        #. User job commands live under system.slice -> slurmd.service
        #. system.slice -> cmd.service --> /cm/local/apps/cmd/sbin/cm-cgroup-job-keepalive


11-october-2024
==================================
1. See bcm_query_description.txt for description of all Prometheus querries


14-october-2024
==================================
1. Multiple ways of collecting metrics
    a) `slurmdbd`
        #. Command = `sacct`
        #. Gives job level data
        #. Does not track GPU usage conveniently
    #) BCM Chargeback
    #) `cmsh` device level
    #) `cmsh` user level
    #) `cmsh` job level
        #. Uses PromQL 
        #. Command 
            * [head01->monitoring->labeledentity]% list|grep 'job_id="1329"'
              [head01->monitoring->labeledentity]% measurables 4b91-1d4e    # Pick the one with 'JobSampler'
              [head01->monitoring->labeledentity]% instantquery job_cpuacct_usage_seconds
              [head01->monitoring->labeledentity]% dumpmonitoringdata -24h now job_cpuacct_usage_seconds 4b91-1d4e
#. busy-cpu-and-mem$ sbatch --cpus-per-task=3 --wrap="./a.out 3 2 1000"
   Submitted batch job 335
    a) [bcm10-h01->monitoring->labeledentity]% instantquery job_cpuacct_usage_seconds
       Failed, status: undefined
       Accounting & Reporting functionality is disabled in your certificate
    #) Evidently, Easy8 license lacks this functionality
#. Fig 12.26 is useful in BCM admin manual
    

QUESTIONS
==================================
1. How did I get charged for GPU(s) when there is no GPU on my machine?
#. Why is 'Memory' so large?
    a) Note units are (GB * s)
    #) FOr the two above jobs :
        #. 180 * 2.25 + 180 * 5.50 = 1395 GBs, which is close enough for me
           accept that it 1.49TBs is the right value
#. Why aren't jobs at XXX running
   /cm/local/apps/cmd/sbin/cm-cgroup-job-keepalive? It does on my cluster
#. In XXX, [bcm10-h01->wlm[bcm10-slurm]->jobs]% measurables 332 returns nothing?
#. In 13.3, where do I find Job Information Retention?
#. Where do I get historical job 'measurable' data?
#. Why are there 3 entities? 
    a) See BCM notes for details
#. In section 14.3, what is the difference between measurables and query?
    a) How do they interact?
#. On DGX (BCM-9.0), why does
    a) busy-cpu-and-mem$ sbatch --partition=dgxq --cpus-per-task=10 --wrap="./a.out 4 20 10000"
    #) Yield 
        [head01->monitoring->labeledentity]% instantquery job_cpuacct_usage_seconds
        Name                       category group    hostname job         job_id   job_name queue    user     wlm      Timestamp                 Value
        -------------------------- -------- -------- -------- ----------- -------- -------- -------- -------- -------- ------------------------- --------------
        job_cpuacct_usage_seconds  dgx1     ali      dgx01    JobSampler  3592     wrap     dgxq     ali      slurm    Mon Oct 14 10:42:58 2024  479.896196086
    #) ANSWER : b/c job_cpuacct_usage_seconds is querried at some interval
#. Why can't I find job_cpuacct_usage_seconds? : 
    a) See : JobSampler entry from 
       [head01->monitoring->labeledentity]% measurables 4b91-1d4e
#. Why can't I find gpu measurables? 
    a) e.g. [head01->monitoring->labeledentity]% measurables 267c-e7a8
#. In location cXXX, why can't I find JobSampler
    a) [head01->monitoring->labeledentity]% measurables 4b91-1d4e
#. In location cXXX, why cant I find measurables
   [head->wlm[slurm]->jobs]% measurables 9436
   No measurables for this started job (yet)
    a) Other jobs don't suffer from this
#. [head01->monitoring->labeledentity]% ls | less -SN 
    a) Seems like data is enphemerally saved, jobs prior to 1952 DNE
#. How is JobSampler linked to job_cpuacct_usage_seconds?  I don't see it in cmsh
