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
from functions import read_data_dir




def main():
    """

    Args

        N/A

    Returns

    Raises

    """

    parser = argparse.ArgumentParser(
                    description="Takes data extracted from cmsh (via collect_data.sh) and trolls through gpu temperatures searching for hot gpus.")
    parser.add_argument('--path', metavar='path/to/toplevel/data/dir', type=str,
                        help='Path to parsable sacct file')
    args = parser.parse_args()
    path = args.path
    read_data_dir(path)
    sys.exit(0)


if __name__ == "__main__":

    main()


