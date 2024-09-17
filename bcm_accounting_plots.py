# Author : Ali Snedden
# Date   : 02/24/24
# License:
#
#
# Goals (ranked by priority) :
#
# Refs :
#   a)
#   #) https://www.nltk.org/book/ch06.html
#
import os
import sys
import random
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer


class Job:
    """Class that maps to a single Slurm job"""

    def __init__(self)

        """Initialize Job Class

        Args :

        Returns :

        Raises :

        """

        self.step = []


class Step:
    """Class that maps to a single Slurm step"""

    def __init__(self, )

        """Initialize Step Class

        Args :

        Returns :

        Raises :

        """


class Batch:
    """Class that maps to the batch script of a Slurm job"""

    def __init__(self, )

        """Initialize Job Class

        Args :

        Returns :

        Raises :

        """


# Expects data like : sacct --allusers -P -S 2024-08-01 --format="jobid,user,partition,alloccpus,elapsed,cputime,state,tres" > sacct_2024-08-01.txt

def main():
    """Loads the sacct movie reviews sentiment analysis dataset.

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
    df = pd.read_csv(path, sep='|')
    sys.stdout.flush()
    sys.exit(0)


if __name__ == "__main__":

    main()


