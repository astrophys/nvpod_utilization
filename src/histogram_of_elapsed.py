# Author : Ali Snedden
# Date   : 01/24/25
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
#matplotlib.use('tkagg')        # Linux
matplotlib.use('qtagg')        # Linux
from classes import User
import matplotlib.pyplot as plt
from plot_funcs import make_pie
from plot_funcs import plot_time_series_mpl
from plot_funcs import plot_time_series_plotly
from functions import make_autopct
from functions import parse_sacct_file
from functions import is_job_in_time_range


# Expects data like : sacct --allusers -P -S 2024-08-01 --format="jobidraw,jobname,user,nodelist,elapsedraw,alloccpus,cputimeraw,maxrss,state,start,end,reqtres" > sacct_2024-08-01.txt

# Run via
#    python -m pdb src/bcm_accounting_plots.py --path data/sacct_2024-05-01_to_2024-10-31.txt --start 2024-05-01T00:00:00 --end 2024-11-01T00:00:00 --plottyp time-series --users all
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
    args = parser.parse_args()
    path = args.path
    df = pd.read_csv(path, sep='|', na_filter=False)

    fig = plt.figure()
    gs = fig.add_gridspec(1,1)
    # cpu
    ax = fig.add_subplot(gs[0,0])
    elapsV = df[df['ElapsedRaw'] >0]
    ax.hist(np.log10(elapsV))
    fig.show()


    ## Extract by time range
    sys.stdout.flush()
    sys.exit(0)


if __name__ == "__main__":

    main()


