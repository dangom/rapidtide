#!/usr/bin/env python
#
#   Copyright 2016 Blaise Frederick
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#
# $Author: frederic $
#       $Date: 2016/06/14 13:51:27 $
#       $Id: showtc,v 1.15 2016/06/14 13:51:27 frederic Exp $
#
from __future__ import print_function
import sys
import platform
from cycler import cycler

import matplotlib

if platform.system() == 'Darwin':
    matplotlib.use('MacOSX')
else:
    matplotlib.use('TkAgg')
import tide_funcs as tide
from scipy import arange

from pylab import plot, legend, show, hold


def usage():
    print("usage: showtc texfilename")
    print("	plots the data in a text file")
    print("")
    print("required arguments:")
    print("	textfilename	- a text file containing one timepoint per line")
    return ()


# get the command line parameters
nargs = len(sys.argv)
if nargs < 2:
    usage()
    exit()

# set default variable values
dolegend = True

# handle required args first
textfilename = []
xvecs = []
yvecs = []
linelabels = []
numfiles = 1
numvecs = 0
textfilename.append(sys.argv[1])
if nargs > 2:
    for i in range(2, nargs):
        numfiles += 1
        textfilename.append(sys.argv[i])

for i in range(0, numfiles):
    print('filename ', i, textfilename[i])
    invecs = tide.readvecs(textfilename[i])
    print('   ', invecs.shape[0], ' columns')
    for j in range(0, invecs.shape[0]):
        print('appending vector number ', j)
        yvecs.append(invecs[j])
        xvecs.append(arange(0.0, len(yvecs[numvecs]), 1.0))
        if invecs.shape[0] > 1:
            linelabels.append(textfilename[i] + '_column' + str(j).zfill(2))
        else:
            linelabels.append(textfilename[i])
        numvecs += 1

colorlist = ['r', 'g', 'b', 'k']
hold(True)
for i in range(0, numvecs):
    plot(xvecs[i], yvecs[i], colorlist[i % len(colorlist)], label=linelabels[i])
if dolegend:
    legend()

show()