# Author : Ali Snedden
# Date   : 10/31/24
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
import matplotlib
import numpy as np
import pandas as pd
matplotlib.use('tkagg')
from typing import List,Dict
import matplotlib.pyplot as plt
from functions import make_autopct
from numpy.typing import ArrayLike

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






