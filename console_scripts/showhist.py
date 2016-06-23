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
#       $Author: frederic $
#       $Date: 2016/06/14 13:51:27 $
#       $Id: showhist,v 1.4 2016/06/14 13:51:27 frederic Exp $
#
from __future__ import print_function
import sys
import getopt
import matplotlib
import platform
import tide_funcs as tide
from pylab import plot, xlabel, ylabel, title, legend, show

if platform.system() == 'Darwin':
    matplotlib.use('MacOSX')
else:
    matplotlib.use('TkAgg')


def usage():
    print("usage: showxy textfilename")
    print("	plots xy data in text file")
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
textfilename = sys.argv[1]

# now check options
try:
    opts, args = getopt.getopt(sys.argv[2:], "x:y:l:t:", ["help"])
except getopt.GetoptError as err:
    # print help information and exit:
    print(str(err))  # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

usexlabel = False
useylabel = False
usetitle = False
uselegend = False
thelegendlabel = ''
thetitle = ''
thexlabel = ''
theylabel = ''

for o, a in opts:
    if o == "-x":
        usexlabel = True
        thexlabel = a
        print("labelling x axis with ", thexlabel)
    elif o == "-y":
        useylabel = True
        theylabel = a
        print("labelling y axis with ", theylabel)
    elif o == "-l":
        uselegend = True
        thelegendlabel = a
        print("using legend ", thelegendlabel)
    elif o == "-t":
        usetitle = True
        thetitle = a
        print("using title ", thetitle)
    else:
        assert False, "unhandled option"

indata = tide.readvecs(textfilename)
xvecs = indata[0, :]
yvecs = indata[1, :]
plot(xvecs, yvecs, 'r')
if uselegend:
    legend(thelegendlabel, loc=1)
if usetitle:
    title(thetitle)
if usexlabel:
    xlabel(thexlabel, fontsize=16, fontweight='bold')
if useylabel:
    ylabel(theylabel, fontsize=16, fontweight='bold')
show()