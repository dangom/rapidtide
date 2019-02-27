#!/usr/bin/env python
from __future__ import print_function, division

import os.path as op

import numpy as np
import pylab as plt

from rapidtide.io import writenpvecs
from rapidtide.filter import noncausalfilter
from rapidtide.correlate import shorttermcorr_1D, shorttermcorr_2D
from rapidtide.tests.utils import get_test_data_path


def test_stcorrelate(debug=False):
    tr = 0.72
    testlen = 800
    shiftdist = 5
    windowtime = 30.0
    stepsize = 5.0
    corrweighting = "none"
    outfilename = op.join(get_test_data_path(), "stcorrtest")
    prewindow = True
    dodetrend = True
    timeaxis = np.arange(0.0, 1.0 * testlen) * tr

    testfilter = noncausalfilter(filtertype="lfo")
    sig1 = testfilter.apply(1.0 / tr, np.random.random(testlen))
    sig2 = np.float64(np.roll(sig1, int(shiftdist)))

    if debug:
        plt.figure()
        plt.plot(sig1)
        plt.plot(sig2)
        legend = ["Original", "Shifted"]
        plt.show()

    times, corrpertime, ppertime = shorttermcorr_1D(
        sig1,
        sig2,
        tr,
        windowtime,
        samplestep=int(stepsize // tr),
        prewindow=prewindow,
        detrendorder=0,
    )
    plength = len(times)
    times, xcorrpertime, Rvals, delayvals, valid = shorttermcorr_2D(
        sig1,
        sig2,
        tr,
        windowtime,
        samplestep=int(stepsize // tr),
        weighting=corrweighting,
        prewindow=prewindow,
        detrendorder=0,
        display=False,
    )
    xlength = len(times)
    writenpvecs(corrpertime, outfilename + "_pearson.txt")
    writenpvecs(ppertime, outfilename + "_pvalue.txt")
    writenpvecs(Rvals, outfilename + "_Rvalue.txt")
    writenpvecs(delayvals, outfilename + "_delay.txt")
    writenpvecs(valid, outfilename + "_mask.txt")


def main():
    test_stcorrelate(debug=True)


if __name__ == "__main__":
    main()
