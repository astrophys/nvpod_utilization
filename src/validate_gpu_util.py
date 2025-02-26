# Author : Ali Snedden
# Date   : 12/04/24
# Goals (ranked by priority) :
#
# Refs :
#   a)
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
import matplotlib.pyplot as plt
from functions import read_gpu_util




def main():
    """

    Args

        N/A

    Returns

    Raises

    """

    parser = argparse.ArgumentParser(
                description="Takes data extracted from cmsh (via collect_data.sh) "
                            "and trolls through gpu utilization.")
    parser.add_argument('--path', metavar='path/to/toplevel/data/dir', type=str,
                        help='Path to parsable sacct file')
    parser.add_argument('--excludenodes', metavar='excludenodes', nargs='?',
                        type=str, help='Exclude nodes from calculation. Useful when'
                                       'considering nodes that have MIGs enabled')
    args = parser.parse_args()


    if args.excludenodes is not None :
        if('[' in args.excludenodes or ']' in args.excludenodes or
           '-' in args.excludenodes):
            raise ValueError("ERROR!!! You must write the full name of each node")
        excludenodeL = args.excludenodes.split(',')
    else :
        excludenodeL = None


    path = args.path
    (cluster2min, cluster1h, cluster1d) = read_gpu_util(path, excludenodeL)
    sys.exit(0)


if __name__ == "__main__":

    main()


