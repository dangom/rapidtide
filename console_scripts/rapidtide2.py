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
# $Date: 2016/06/14 14:05:01 $
# $Id: rapidtide,v 1.158 2016/06/14 14:05:01 frederic Exp $
#
#
#

from __future__ import print_function, division

import time
import getopt
import platform
import bisect
import warnings
import sys

from sklearn.decomposition import FastICA, PCA

import tide_funcs as tide

from pylab import figure, plot, show
import numpy as np
from statsmodels.tsa.stattools import pacf_yw
from scipy.stats.stats import pearsonr


# if platform.system() == 'Darwin':
#    matplotlib.use('MacOSX')
# else:
#    matplotlib.use('TkAgg')
# from memory_profiler import profile


def version():
    return '$Id: rapidtide,v 1.158 2016/06/14 14:05:01 frederic Exp $'


def startendcheck(timepoints, startpoint, endpoint):
    if startpoint > timepoints - 1:
        print('startpoint is too large (maximum is ', timepoints - 1, ')')
        sys.exit()
    if startpoint < 0:
        realstart = 0
        print('startpoint set to minimum, (0)')
    else:
        realstart = startpoint
    if endpoint > timepoints - 1:
        realend = timepoints - 1
        print('endppoint set to maximum, (', timepoints - 1, ')')
    else:
        realend = endpoint
    if realstart >= realend:
        print('endpoint (', realend, ') must be greater than startpoint (', realstart, ')')
        sys.exit()
    return realstart, realend


def getNullDistributionData(indata, corrscale, ncprefilter, oversampfreq, corrorigin, lagmininpts, lagmaxinpts,
                            optiondict):
    print('\tEstimating significance from ' + str(optiondict['numestreps']) + ' repetitions')
    corrlist = np.zeros((optiondict['numestreps']))

    for i in range(0, optiondict['numestreps']):
        # make a shuffled copy of the regressors
        shuffleddata = np.random.permutation(indata)

        # crosscorrelate with original
        thexcorr = onecorrelation(shuffleddata, oversampfreq, corrorigin, lagmininpts, lagmaxinpts, ncprefilter, indata,
                                  optiondict)

        # fit the correlation
        maxindex, maxlag, maxval, maxsigma, maskval, failreason = \
            onecorrfit(thexcorr, corrscale[corrorigin - lagmininpts:corrorigin + lagmaxinpts], optiondict)

        # find and tabulate correlation coefficient at optimal lag
        corrlist[i] = maxval

        # progress
        tide.progressbar(i + 1, optiondict['numestreps'], label='Percent complete')

    # jump to line after progress bar
    print()

    # return the distribution data
    return corrlist


def onecorrelation(thetc, oversampfreq, corrorigin, lagmininpts, lagmaxinpts, ncprefilter, referencetc, optiondict):
    thetc_classfilter = ncprefilter.apply(oversampfreq, thetc)
    thetc = thetc_classfilter

    # prepare timecourse by normalizing, detrending, and applying a hamming window
    preppedtc = tide.corrnormalize(thetc, optiondict['usewindowfunc'], optiondict['dodetrend'])

    # now actually do the correlation
    if optiondict['gccphat']:
        thexcorr = tide.gccphat(preppedtc, referencetc, False)
    else:
        thexcorr = tide.fastcorrelate(preppedtc, referencetc, usefft=True)
    return thexcorr[corrorigin - lagmininpts:corrorigin + lagmaxinpts]


# @profile(precision=4)
def correlationpass(fmridata, referencetc,
                    fmri_x, os_fmri_x,
                    tr,
                    corrorigin, lagmininpts, lagmaxinpts,
                    corrmask, corrout, meanval,
                    ncprefilter,
                    optiondict):
    corrmask[:] = tide.makemask(np.mean(fmridata, axis=1), threshpct=1.0)
    oversampfreq = optiondict['oversampfactor'] / tr
    inputshape = np.shape(fmridata)
    volumetotal = 0
    reportstep = 1000
    for vox in range(0, inputshape[0]):
        if vox % reportstep == 0 or vox == inputshape[0] - 1:
            tide.progressbar(vox + 1, inputshape[0], label='Percent complete')
        if corrmask[vox] > 0.0:
            if optiondict['oversampfactor'] >= 1:
                thetc = 1.0 * tide.doresample(fmri_x, fmridata[vox, :], os_fmri_x, method=optiondict['interptype'])
            else:
                thetc = 1.0 * (fmridata[vox, :])
            meanval[vox] = np.mean(thetc)
            corrout[vox, :] = onecorrelation(thetc, oversampfreq, corrorigin, lagmininpts, lagmaxinpts, ncprefilter,
                                             referencetc, optiondict)
            volumetotal += 1
    print('\nCorrelation performed on ' + str(volumetotal) + ' voxels')
    return volumetotal


# @profile(precision=4)
def onecorrfit(thetc, corrscale, optiondict, displayplots=False):
    if optiondict['biphasic']:
        if max(thetc) < -1.0 * min(thetc):
            flipfac = -1.0
        else:
            flipfac = 1.0
    else:
        flipfac = 1.0
    if not optiondict['fixdelay']:
        maxindex, maxlag, maxval, maxsigma, maskval, failreason = tide.findmaxlag(
            corrscale,
            flipfac * thetc,
            optiondict['lagmin'], optiondict['lagmax'], optiondict['widthlimit'],
            edgebufferfrac=optiondict['edgebufferfrac'],
            threshval=optiondict['lthreshval'],
            uthreshval=optiondict['uthreshval'],
            debug=optiondict['debug'],
            refine=optiondict['gaussrefine'],
            maxguess=0.0,
            useguess=optiondict['useguess'],
            fastgauss=optiondict['fastgauss'],
            enforcethresh=optiondict['enforcethresh'],
            displayplots=displayplots)
    else:
        # do something different
        failreason = 0
        maxindex = 0
        maxlag = optiondict['fixeddelayvalue']
        maxindex = bisect.bisect_left(corrscale, optiondict['fixeddelayvalue'])
        maxval = flipfac * thetc[maxindex]
        maxsigma = 1.0
        maskval = 1

    return maxindex, maxlag, maxval, maxsigma, maskval, failreason


# @profile(precision=4)
def fitcorr(genlagtc, initial_fmri_x, lagtc, tr,
            threshval, corrscale, corrmask, lagmask, lagtimes, lagstrengths, lagsigma, corrout, meanval, gaussout,
            R2, optiondict):
    FML_BADAMP = 0x01
    FML_BADLAG = 0x02
    FML_BADWIDTH = 0x04
    FML_HITEDGE = 0x08
    FML_FITFAIL = 0x0f
    displayplots = False
    inputshape = np.shape(corrout)
    volumetotal = 0
    ampfails = 0
    lagfails = 0
    widthfails = 0
    edgefails = 0
    fitfails = 0
    sliceoffsettime = 0.0
    reportstep = 1000
    zerolagtc = genlagtc.yfromx(initial_fmri_x)

    for vox in range(0, inputshape[0]):
        if vox % reportstep == 0 or vox == inputshape[0] - 1:
            tide.progressbar(vox + 1, inputshape[0], label='Percent complete')
        if corrmask[vox] > 0.0:
            # sliceoffsettime = tide.calcsliceoffset(optiondict['sliceorder'], i, numslices, tr)
            maxindex, maxlag, maxval, maxsigma, maskval, failreason = onecorrfit(corrout[vox, :], corrscale, optiondict,
                                                                                 displayplots=displayplots)

            if maxval > 0.3:
                displayplots = False

            # question - should maxlag be added or subtracted?  As of 10/18, it is subtracted
            #  potential answer - tried adding, results are terrible.
            lagtc[vox, :] = genlagtc.yfromx(initial_fmri_x - maxlag)

            # now tuck everything away in the appropriate output array
            lagmask[vox] = maskval
            if maskval > 0:
                volumetotal += 1
                lagtimes[vox] = maxlag
                lagstrengths[vox] = maxval
                lagsigma[vox] = maxsigma
                if not optiondict['fixdelay']:
                    gaussout[vox, :] = tide.gauss_eval(corrscale, [maxval, maxlag, maxsigma])
                R2[vox] = lagstrengths[vox] * lagstrengths[vox]
            else:
                lagtimes[vox] = 0.0
                lagstrengths[vox] = 0.0
                lagsigma[vox] = 0.0
                gaussout[vox, :] = 0.0
                R2[vox] = 0.0
                if failreason & FML_BADAMP:
                    ampfails += 1
                if failreason & FML_BADLAG:
                    lagfails += 1
                if failreason & FML_BADWIDTH:
                    widthfails += 1
                if failreason & FML_HITEDGE:
                    edgefails += 1
                if failreason & FML_FITFAIL:
                    fitfails += 1
        else:
            lagtc[vox, :] = zerolagtc
            lagtimes[vox] = 0.0
            lagstrengths[vox] = 0.0
            lagsigma[vox] = 0.0
            gaussout[vox, :] = 0.0
            R2[vox] = 0.0
    print('\nCorrelation fitted in ' + str(volumetotal) + ' voxels')
    print('\tampfails=', ampfails, ' lagfails=', lagfails, ' widthfail=', widthfails, ' edgefail=', edgefails,
          ' fitfail=', fitfails)

    return volumetotal


# @profile(precision=4)
def refineregressor(fmridata, fmritr, shiftedtcs, maskarray, lagstrengths, lagtimes, lagsigma, R2, theprefilter,
                    optiondict, padtrs=60, includemask=None, excludemask=None):
    inputshape = np.shape(fmridata)
    outputdata = np.zeros(inputshape[1])
    ampmask = np.where(lagstrengths >= optiondict['ampthresh'], 1, 0)
    if optiondict['lagmaskside'] == 'upper':
        delaymask = \
            np.where(lagtimes > optiondict['lagminthresh'], 1, 0) * \
            np.where(lagtimes < optiondict['lagmaxthresh'], 1, 0)
    elif optiondict['lagmaskside'] == 'lower':
        delaymask = \
            np.where(lagtimes < -optiondict['lagminthresh'], 1, 0) * \
            np.where(lagtimes > -optiondict['lagmaxthresh'], 1, 0)
    else:
        abslag = abs(lagtimes)
        delaymask = \
            np.where(abslag > optiondict['lagminthresh'], 1, 0) * \
            np.where(abslag < optiondict['lagmaxthresh'], 1, 0)
    sigmamask = np.where(lagsigma < optiondict['sigmathresh'], 1, 0)
    locationmask = 0 * ampmask + 1
    if includemask is not None:
        locationmask = locationmask * includemask
    if excludemask is not None:
        locationmask = locationmask * excludemask
    print('location mask created')

    # first generate the refine mask
    locationfails = np.sum(1 - locationmask)
    ampfails = np.sum(1 - ampmask)
    lagfails = np.sum(1 - delaymask)
    sigmafails = np.sum(1 - sigmamask)
    maskarray = locationmask * ampmask * delaymask * sigmamask
    volumetotal = np.sum(maskarray)
    reportstep = 1000

    # now do the refinement using the valid voxels
    for vox in range(0, inputshape[0]):
        if vox % reportstep == 0 or vox == inputshape[0] - 1:
            tide.progressbar(vox + 1, inputshape[0], label='Percent complete (timeshifting)')
        if maskarray[vox] == 1:
            themean = np.mean(fmridata[vox, :])
            if themean != 0.0:
                normfac = 1.0 / themean
            else:
                normfac = 0.0
            if optiondict['refineweighting'] == 'R':
                thisweight = normfac * lagstrengths[vox]
            elif optiondict['refineweighting'] == 'R2':
                thisweight = normfac * R2[vox]
            else:
                thisweight = normfac
            if optiondict['dodetrend']:
                normtc = tide.detrend(fmridata[vox, :] * thisweight, demean=True)
            else:
                normtc = fmridata[vox, :] * thisweight
            shifttrs = -(-optiondict['offsettime'] + lagtimes[vox]) / fmritr  # lagtimes is in seconds
            [shiftedtc, weights, paddedshiftedtc, paddedweights] = tide.timeshift(normtc, shifttrs, padtrs)
            if optiondict['filterbeforePCA']:
                shiftedtcs[vox, :] = theprefilter.apply(optiondict['fmrifreq'], shiftedtc)
            else:
                shiftedtcs[vox, :] = 1.0 * shiftedtc
    print()

    # now generate the refined timecourse
    refinevoxels = shiftedtcs[np.where(maskarray > 0)]
    averagedata = np.sum(refinevoxels, axis=0) / volumetotal
    if optiondict['estimatePCAdims']:
        pcacomponents = 'mle'
    else:
        pcacomponents = 1
    icacomponents = 1

    if optiondict['refinetype'] == 'ica':
        print('performing ica refinement')
        thefit = FastICA(n_components=icacomponents).fit(refinevoxels)  # Reconstruct signals
        print('Using first of ', len(thefit.components_), ' components')
        icadata = thefit.components_[0]
        filteredavg = tide.corrnormalize(theprefilter.apply(optiondict['fmrifreq'], averagedata), True, True)
        filteredica = tide.corrnormalize(theprefilter.apply(optiondict['fmrifreq'], icadata), True, True)
        thepxcorr = pearsonr(filteredavg, filteredica)[0]
        print('ica/avg correlation = ', thepxcorr)
        if thepxcorr > 0.0:
            outputdata = 1.0 * icadata
        else:
            outputdata = -1.0 * icadata
    elif optiondict['refinetype'] == 'pca':
        print('performing pca refinement')
        thefit = PCA(n_components=pcacomponents).fit(refinevoxels)
        print('Using first of ', len(thefit.components_), ' components')
        pcadata = thefit.components_[0]
        filteredavg = tide.corrnormalize(theprefilter.apply(optiondict['fmrifreq'], averagedata), True, True)
        filteredpca = tide.corrnormalize(theprefilter.apply(optiondict['fmrifreq'], pcadata), True, True)
        thepxcorr = pearsonr(filteredavg, filteredpca)[0]
        print('pca/avg correlation = ', thepxcorr)
        if thepxcorr > 0.0:
            outputdata = 1.0 * pcadata
        else:
            outputdata = -1.0 * pcadata
    else:
        print('performing averaging refinement')
        outputdata = averagedata
    print()
    print(str(
        volumetotal) + ' voxels used for refinement:',
        '\n	', locationfails, ' locationfails',
        '\n	', ampfails, ' ampfails',
        '\n	', lagfails, ' lagfails',
        '\n	', sigmafails, ' sigmafails')

    return volumetotal, outputdata


def maketmask(filename, timeaxis, maskvector):
    inputdata = tide.readvecs(filename)
    theshape = np.shape(inputdata)
    for idx in range(0, theshape[1]):
        starttime = inputdata[0, idx]
        endtime = starttime + inputdata[1, idx]
        startindex = np.max((bisect.bisect_left(timeaxis, starttime), 0))
        endindex = np.min((bisect.bisect_right(timeaxis, endtime), len(maskvector) - 1))
        maskvector[startindex:endindex] = 1.0
        print(starttime, startindex, endtime, endindex)
    if False:
        fig = figure()
        ax = fig.add_subplot(111)
        ax.set_title('temporal mask vector')
        plot(timeaxis, maskvector)
        show()
    return maskvector


def prewhiten(indata, arcoffs):
    pwdata = 1.0 * indata
    for i in range(0, len(arcoffs)):
        pwdata[(i + 1):] = pwdata[(i + 1):] + arcoffs[i] * indata[:(-1 - i)]
    return pwdata


def getglobalsignal(indata, optiondict, includemask=None, excludemask=None):
    # mask to interesting voxels
    themask = tide.makemask(np.mean(indata, axis=1), threshpct=1.0)
    if includemask is not None:
        themask = themask * includemask
    if excludemask is not None:
        themask = themask * excludemask

    # add up all the voxels
    globalmean = 0.0 * indata[0, :]
    thesize = np.shape(themask)
    numvoxelsused = 0
    for vox in range(0, thesize[0]):
        if themask[vox] > 0.0:
            numvoxelsused += 1
            if optiondict['meanscaleglobal']:
                themean = np.mean(indata[vox, :])
                if themean != 0.0:
                    globalmean = globalmean + indata[vox, :] / themean - 1.0
            else:
                globalmean = globalmean + indata[vox, :]
    print()
    print('used ', numvoxelsused, ' voxels to calculate global mean signal')
    return tide.stdnormalize(globalmean)


def usage(argstyle):
    if argstyle == 'old':
        print("usage: rapidtide inputfile inputsamprate inputstarttime fmrifilename sliceorder numskip outputname ")
    else:
        print("usage: rapidtide2 fmrifilename outputname ")
    print("[-r LAGMIN,LAGMAX] [-s SIGMALIMIT] [-a] [--nowindow] [-G] [-f GAUSSSIGMA] [-O oversampfac] [-t TRvalue] "
          "[-d] [-b] [-V] [-L] [-R] [-C] [-F LOWERFREQ,UPPERFREQ[,LOWERSTOP,UPPERSTOP]] [-o OFFSETTIME]"
          " [-T] [-p] [-P] [-A ORDER] [-B] [-h HISTLEN] [-i INTERPTYPE] [-I] [-Z DELAYTIME] [-N NREPS]"
          "[--refineweighting=REFINETYPE] [--refinepasses=NUMPASSES] [--excludemask=MASKNAME] [--includemask=MASKNAME] "
          "[--lagminthresh=LAGMINTHRESH] [--lagmaxthresh=LAGMAXTHRESH] [--ampthresh=AMPTHRESH]"
          "[--sigmathresh=SIGMATHRESH] [--refineoffset] [--pca] [--ica] [--refineupperlag] [--refinelowerlag] [--tmask=MASKFILE]"
          "[--limitoutput] [--timerange=STARTPOINT,ENDPOINT] ")
    if argstyle == 'old':
        print("")
        print("required arguments:")
        print("    inputfile    - the name of the reference regressor text file")
        print("    inputsamprate    - the sample rate of the reference regressor, in Hz")
        print("    inputstarttime   - the time delay, in seconds, into the inputfile that")
        print("                       matches the start time of the fmrifile")
        print("    fmrifilename    - the BOLD fmri file")
        print("    sliceorder    - the slice acquisition order used (6 is Siemens interleave)")
        print("    numskip        - the number of tr periods previously deleted during")
        print("                     preprocessing")
        print("    outputname    - the root name for the output files")
        print("")
    else:
        print(
            "[--numskip=SKIP] [--sliceorder=ORDER] [--regressorfreq=FREQ] [--regressor=FILENAME] [--regressorstart=STARTTIME]")
        print("")
        print("required arguments:")
        print("    fmrifilename    - the BOLD fmri file")
        print("    outputname    - the root name for the output files")
    print("")
    print("preprocessing options:")
    print("    -t TRvalue       - override the TR in the fMRI file with the value ")
    print("                       TRvalue")
    print("    -a               - disable antialiasing filter")
    print("    --nodetrend      - disable linear trend removal")
    print("    -I               - invert the sign of the regressor before processing")
    print("    -i               - use specified interpolation type (options are 'cubic',")
    print("                       'quadratic', and 'univariate (default)')")
    print("    -o               - apply an offset OFFSETTIME to the lag regressors")
    print("    -b               - use butterworth filter for band splitting instead of")
    print("                       trapezoidal FFT filter")
    print("    -F               - filter data and regressors from LOWERFREQ to UPPERFREQ.")
    print("                       LOWERSTOP and UPPERSTOP can be specified, or will be")
    print("                       calculated automatically")
    print("    -V               - filter data and regressors to VLF band")
    print("    -L               - filter data and regressors to LFO band")
    print("    -R               - filter data and regressors to respiratory band")
    print("    -C               - filter data and regressors to cardiac band")
    print("    -N               - estimate significance threshold by running NREPS null ")
    print("                       correlations (default is 10000, set to 0 to disable)")
    print("    --nowindow       - disable precorrelation windowing")
    print("    -f GAUSSSIGMA    - spatially filter fMRI data prior to analysis using ")
    print("                       GAUSSSIGMA in mm")
    print("    -M               - generate a global mean regressor and use that as the ")
    print("                       reference regressor")
    print("    -m               - mean scale regressors during global mean estimation")
    if argstyle == 'new':
        print("    --sliceorder     - use ORDER as slice acquisition order used (6 is Siemens ")
        print("                       interleave, default is 0 (do nothing))")
        print("    --numskip SKIP   - SKIP tr's were previously deleted during preprocessing")
    print("                        (default is 0)")
    print("")
    print("correlation options:")
    print("    -O OVERSAMPFAC      - oversample the fMRI data by the following integral ")
    print("                       factor (default is 2)")
    if argstyle == 'new':
        print("    --regressor      - Read probe regressor from file FILENAME (if none ")
        print("                       specified, generate and use global regressor)")
        print("    --regressorfreq  - Probe regressor in file has sample frequency FREQ ")
        print("                       (default is 1/tr)")
        print("    --regressorstart - First TR of fmri file occurs at time STARTTIME ")
        print("                       in the regressor file (default is 0.0)")
    print("    -G               - use generalized cross-correlation with phase alignment ")
    print("                       transform (GCC-PHAT) instead of correlation")
    print("")
    print("correlation fitting options:")
    print("    -Z DELAYTIME     - don't fit the delay time - set it to DELAYTIME seconds ")
    print("                       for all voxels")
    print("    -r LAGMIN,LAGMAX - limit fit to a range of lags from LAGMIN to LAGMAX")
    print("    -s SIGMALIMIT    - reject lag fits with linewidth wider than SIGMALIMIT")
    print("")
    print("regressor refinement options:")
    print("    --refineweighting  - apply REFINETYPE weighting to each timecourse prior ")
    print("                         to refinement (valid weightings are 'None', ")
    print("                         'R', 'R2' (default)")
    print("    --refinepasses     - set the number of refinement passes to NUMPASSES ")
    print("                         (default is 1)")
    print("    --includemask      - only use voxels in MASKNAME for global regressor ")
    print("                         generation and regressor refinement")
    print("    --excludemask      - do not use voxels in MASKNAME for global regressor ")
    print("                         generation and regressor refinement")
    print("    --lagminthresh     - for refinement, exclude voxels with delays less ")
    print("                         than LAGMINTHRESH (default is 1.5s)")
    print("    --lagmaxthresh     - for refinement, exclude voxels with delays greater ")
    print("                         than LAGMAXTHRESH (default is 1000s)")
    print("    --ampthresh        - for refinement, exclude voxels with correlation ")
    print("                         coefficients less than AMPTHRESH (default is 0.3)")
    print("    --sigmathresh      - for refinement, exclude voxels with widths greater ")
    print("                         than SIGMATHRESH (default is 50s)")
    print("    --refineoffset     - adjust offset time during refinement to bring peak ")
    print("                         delay to zero")
    print("    --refineupperlag   - only use positive lags for regressor refinement")
    print("    --refinelowerlag   - only use negative lags for regressor refinement")
    print("    --pca              - use pca to derive refined regressor (default is ")
    print("                         averaging)")
    print("    --ica              - use ica to derive refined regressor (default is ")
    print("                         averaging)")
    print("")
    print("output options:")
    print("    --limitoutput    - don't save some of the large and rarely used files")
    print("    -T               - save a table of lagtimes used")
    print("    -h HISTLEN       - change the histogram length to HISTLEN (default is")
    print("                       100)")
    print("    --timerange      - limit analysis to data between timepoints STARTPOINT ")
    print("                       and ENDPOINT in the fmri file")
    print("    --noglm          - turn off GLM filtering to remove delayed regressor ")
    print("                       from each voxel (disables output of rCBV)")
    print("")
    print("miscellaneous options:")
    print("    -c               - data file is a converted CIFTI")
    print("    -S               - simulate a run - just report command line options")
    print("    -d               - display plots of interesting timecourses")
    print("")
    print("experimental options (not fully tested, may not work):")
    print("    --tmask=MASKFILE - only correlate during epochs specified in ")
    print("                       MASKFILE (NB: each line of MASKFILE contains the ")
    print("                       time and duration of an epoch to include")
    print("    -p               - prewhiten and refit data")
    print("    -P               - save prewhitened data (turns prewhitening on)")
    print("    -A, --AR         - set AR model order to ORDER (default is 1)")
    print("    -B               - biphasic mode - match peak correlation ignoring sign")
    return ()


def main():
    # set default variable values
    optiondict = {}

    # input file options
    optiondict['isgrayordinate'] = False

    # preprocessing options
    optiondict['dogaussianfilter'] = False  # apply a spatial filter to the fmri data prior to analysis
    optiondict['gausssigma'] = 0.0  # the width of the spatial filter kernel in mm
    optiondict['antialias'] = True  # apply an antialiasing filter to any regressors prior to filtering
    optiondict['invertregressor'] = False  # invert the initial regressor during startup
    optiondict['sliceorder'] = 0  # do not apply any slice order correction by default
    optiondict['startpoint'] = -1  # by default, analyze the entire length of the dataset
    optiondict['endpoint'] = 10000000  # by default, analyze the entire length of the dataset
    optiondict['preprocskip'] = 0  # number of trs skipped in preprocessing

    # correlation options
    optiondict['dodemean'] = True  # remove the mean from signals prior to correlation
    optiondict['dodetrend'] = True  # remove linear trends prior to correlation
    optiondict['usewindowfunc'] = True  # apply a hamming window prior to correlation
    optiondict['gccphat'] = False  # use a phase alignment transform rather than crosscorrelation
    optiondict['usetmask'] = False  # premultiply the regressor with the tmask timecourse
    optiondict['tmaskname'] = ''  # file name for tmask regressor

    # correlation fitting options
    optiondict['biphasic'] = False  # find peak with highest magnitude, regardless of sign
    optiondict['gaussrefine'] = True  # fit gaussian after initial guess at parameters
    optiondict['fastgauss'] = False  # use a non-iterative gaussian peak fit (DOES NOT WORK)
    optiondict['lthreshval'] = 0.0  # zero out peaks with correlations lower than this value
    optiondict['uthreshval'] = 1.0  # zero out peaks with correlations higher than this value
    optiondict['edgebufferfrac'] = 0.0  # what fraction of the correlation window to avoid on either end when fitting
    optiondict['useguess'] = False  # supply an initial guess for the correlation peak location

    # postprocessing options
    optiondict['doglmfilt'] = True  # use a glm filter to remove the delayed regressor from the data in each voxel
    optiondict['doprewhiten'] = False  # prewhiten the data (I have no idea if this works)
    optiondict['armodelorder'] = 1  # AR model order for prewhitening the data (I have no idea if this works)

    # filter options
    optiondict['zpfilter'] = True
    optiondict['trapezoidalfftfilter'] = True
    optiondict['usebutterworthfilter'] = False
    optiondict['filtorder'] = 3
    optiondict['padseconds'] = 30.0  # the number of seconds of padding to add to each end of a filtered timecourse

    # output options
    optiondict['savelagregressors'] = True
    optiondict['saveglmfiltered'] = True
    optiondict['saveprewhiten'] = False
    optiondict['savecorrtimes'] = False

    optiondict['interptype'] = 'univariate'
    optiondict['useglobalref'] = False
    optiondict['fixdelay'] = False
    optiondict['fixeddelayvalue'] = 0.0

    # significance estimation options
    optiondict['estimate_significance'] = True
    optiondict['numestreps'] = 10000
    optiondict['nohistzero'] = False
    optiondict['ampthreshfromsig'] = True
    optiondict['sighistlen'] = 100

    optiondict['histlen'] = 250
    optiondict['oversampfactor'] = 2
    optiondict['lagmin'] = -30.0
    optiondict['lagmax'] = 30.0
    optiondict['widthlimit'] = 100.0
    optiondict['offsettime'] = 0.0
    optiondict['offsettime_total'] = 0.0
    optiondict['arb_lower'] = 0.05
    optiondict['arb_upper'] = 0.20
    optiondict['addedskip'] = 0

    # refinement options
    optiondict['meanscaleglobal'] = False
    optiondict['lagmaskside'] = 'both'
    optiondict['refineweighting'] = 'R2'
    optiondict['sigmathresh'] = 100.0
    optiondict['lagminthresh'] = 1.5
    optiondict['lagmaxthresh'] = 1000.0
    optiondict['ampthresh'] = 0.3
    optiondict['dorefineregressor'] = False
    optiondict['refinepasses'] = 1
    optiondict['refineoffset'] = False
    optiondict['excludemaskname'] = None
    optiondict['includemaskname'] = None
    optiondict['refinetype'] = 'averaging'
    optiondict['estimatePCAdims'] = False
    optiondict['filterbeforePCA'] = True
    optiondict['fmrifreq'] = 0.0

    # debugging options
    optiondict['fakerun'] = False
    optiondict['displayplots'] = False
    optiondict['debug'] = False
    optiondict['enforcethresh'] = True
    optiondict['verbose'] = False
    optiondict['version_rapidtide'] = version()
    optiondict['version_tideuncs'] = tide.version()

    realtr = 0.0
    theprefilter = tide.noncausalfilter()
    theprefilter.setbutter(optiondict['usebutterworthfilter'], optiondict['filtorder'])

    # start the clock!
    timings = [['Start', time.time(), None, None]]

    # get the command line parameters
    filename = None
    inputfreq = None
    inputstarttime = None
    if sys.argv[0].endswith('rapidtide'):
        print('called as rapidtide, using old style arguments')
        optiondict['argstyle'] = 'old'
        if len(sys.argv) < 8:
            usage(optiondict['argstyle'])
            sys.exit()
        # handle required args first
        filename = sys.argv[1]
        inputfreq = float(sys.argv[2])
        inputstarttime = float(sys.argv[3])
        fmrifilename = sys.argv[4]
        optiondict['sliceorder'] = int(sys.argv[5])
        optiondict['preprocskip'] = int(sys.argv[6])
        outputname = sys.argv[7]
        optparsestart = 8
    elif sys.argv[0].endswith('rapidtide2'):
        print('called as rapidtide2, using new style arguments')
        optiondict['argstyle'] = 'new'
        if len(sys.argv) < 3:
            usage(optiondict['argstyle'])
            sys.exit()
        # handle required args first
        fmrifilename = sys.argv[1]
        outputname = sys.argv[2]
        optparsestart = 3
    else:
        print('unhandled option - called as ', sys.argv[0])
        sys.exit()

    # now scan for optional arguments
    try:
        opts, args = getopt.getopt(sys.argv[optparsestart:], 'abcdf:gh:i:mo:ps:r:t:vBCF:GILMN:O:PRSTVZ:', ['help',
                                                                                                           'nowindow',
                                                                                                           'lagminthresh=',
                                                                                                           'lagmaxthresh=',
                                                                                                           'ampthresh=',
                                                                                                           'sigmathresh=',
                                                                                                           'refineweighting=',
                                                                                                           'refinepasses=',
                                                                                                           'includemask=',
                                                                                                           'excludemask=',
                                                                                                           'refineoffset',
                                                                                                           'pca',
                                                                                                           'ica',
                                                                                                           'noglm',
                                                                                                           'tmask=',
                                                                                                           'nodetrend',
                                                                                                           'sliceorder=',
                                                                                                           'numskip=',
                                                                                                           'limitoutput',
                                                                                                           'regressor=',
                                                                                                           'regressorfreq=',
                                                                                                           'regressorstart=',
                                                                                                           'timerange=',
                                                                                                           'refineupperlag',
                                                                                                           'refinelowerlag',
                                                                                                           'fastgauss',
                                                                                                           'nogaussrefine',
                                                                                                           'AR='])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))  # will print something like 'option -a not recognized'
        usage(optiondict['argstyle'])
        sys.exit(2)

    formattedcmdline = [sys.argv[0] + ' \\']
    for thearg in range(1, optparsestart):
        formattedcmdline.append('\t' + sys.argv[thearg] + ' \\')

    for o, a in opts:
        linkchar = ' '
        if o == '--nowindow':
            optiondict['usewindowfunc'] = False
            print('disable precorrelation windowing')
        elif o == '-v':
            optiondict['verbose'] = True
            print('Turned on verbose mode')
        elif o == '-G':
            optiondict['gccphat'] = True
            optiondict['dodetrend'] = True
            print('Enabled GCC-PHAT fitting')
        elif o == '-I':
            optiondict['invertregressor'] = True
            print('Invert the regressor prior to running')
        elif o == '-B':
            optiondict['biphasic'] = True
            print('Enabled biphasic correlation fitting')
        elif o == '-S':
            optiondict['fakerun'] = True
            print('report command line options and quit')
        elif o == '-a':
            optiondict['antialias'] = False
            print('antialiasing disabled')
        elif o == '-M':
            optiondict['useglobalref'] = True
            print('using global mean timecourse as the reference regressor')
        elif o == '-m':
            optiondict['meanscaleglobal'] = True
            print('mean scale voxels prior to generating global mean')
        elif o == '--limitoutput':
            optiondict['savelagregressors'] = False
            optiondict['saveglmfiltered'] = False
            print('disabling output of lagregressors and glm filtered timecourses')
        elif o == '--noglm':
            optiondict['doglmfilt'] = False
            print('disabling GLM filter')
        elif o == '-T':
            optiondict['savecorrtimes'] = True
            print('saving a table of correlation times used')
        elif o == '-V':
            theprefilter.settype('vlf')
            print('prefiltering to vlf band')
        elif o == '-L':
            theprefilter.settype('lfo')
            print('prefiltering to lfo band')
        elif o == '-R':
            theprefilter.settype('resp')
            print('prefiltering to respiratory band')
        elif o == '-C':
            theprefilter.settype('cardiac')
            print('prefiltering to cardiac band')
        elif o == '-F':
            arbvec = a.split(',')
            if len(arbvec) != 2 and len(arbvec) != 4:
                usage(optiondict['argstyle'])
                sys.exit()
            if len(arbvec) == 2:
                optiondict['arb_lower'] = float(arbvec[0])
                optiondict['arb_upper'] = float(arbvec[1])
                optiondict['arb_lowerstop'] = 0.9 * float(arbvec[0])
                optiondict['arb_upperstop'] = 1.1 * float(arbvec[1])
            if len(arbvec) == 4:
                optiondict['arb_lower'] = float(arbvec[0])
                optiondict['arb_upper'] = float(arbvec[1])
                optiondict['arb_lowerstop'] = float(arbvec[2])
                optiondict['arb_upperstop'] = float(arbvec[3])
            theprefilter.settype('arb')
            theprefilter.setarb(optiondict['arb_lowerstop'], optiondict['arb_lower'],
                                optiondict['arb_upper'], optiondict['arb_upperstop'])
            print('prefiltering to ', optiondict['arb_lower'], optiondict['arb_upper'],
                  '(stops at ', optiondict['arb_lowerstop'], optiondict['arb_upperstop'], ')')
        elif o == '-p':
            optiondict['doprewhiten'] = True
            print('prewhitening data')
        elif o == '-P':
            optiondict['doprewhiten'] = True
            optiondict['saveprewhiten'] = True
            print('saving prewhitened data')
        elif o == '-d':
            optiondict['displayplots'] = True
            print('displaying all plots')
        elif o == '-N':
            optiondict['numestreps'] = int(a)
            if optiondict['numestreps'] == 0:
                optiondict['estimate_significance'] = False
                print('Will not estimate significance thresholds from null correlations')
            else:
                print('Will estimate p<0.05 significance threshold from ', optiondict['numestreps'],
                      ' null correlations')
        elif o == '-s':
            optiondict['widthlimit'] = float(a)
            print('Setting gaussian fit width limit to ', optiondict['widthlimit'], 'Hz')
        elif o == '-b':
            theprefilter.setbutter(True, optiondict['filtorder'])
            print('Using butterworth bandlimit filter')
        elif o == '-Z':
            optiondict['fixeddelayvalue'] = float(a)
            optiondict['fixdelay'] = True
            optiondict['lagmin'] = optiondict['fixeddelayvalue'] - 10.0
            optiondict['lagmax'] = optiondict['fixeddelayvalue'] + 10.0
            print('Delay will be set to ', optiondict['fixeddelayvalue'], 'in all voxels')
        elif o == '-f':
            optiondict['gausssigma'] = float(a)
            optiondict['dogaussianfilter'] = True
            print('Will prefilter fMRI data with a gaussian kernel of ', optiondict['gausssigma'], ' mm')
        elif o == '--timerange':
            limitvec = a.split(',')
            optiondict['startpoint'] = int(limitvec[0])
            optiondict['endpoint'] = int(limitvec[1])
            linkchar = '='
            print('Analysis will be performed only on data from point ', optiondict['startpoint'], ' to ',
                  optiondict['endpoint'])
        elif o == '-r':
            lagvec = a.split(',')
            if not optiondict['fixdelay']:
                optiondict['lagmin'] = float(lagvec[0])
                optiondict['lagmax'] = float(lagvec[1])
                print('Correlations will be calculated over range ', optiondict['lagmin'], ' to ', optiondict['lagmax'])
        elif o == '-y':
            optiondict['interptype'] = a
            if (optiondict['interptype'] != 'cubic') and (optiondict['interptype'] != 'quadratic') and (
                        optiondict['interptype'] != 'univariate'):
                print('unsupported interpolation type!')
                sys.exit()
        elif o == '-h':
            optiondict['histlen'] = int(a)
            print('Setting histogram length to ', optiondict['histlen'])
        elif o == '-o':
            optiondict['offsettime'] = float(a)
            optiondict['offsettime_total'] = float(a)
            print('Applying a timeshift of ', optiondict['offsettime'], ' to regressor')
        elif o == '-t':
            realtr = float(a)
            print('TR value forced to ', realtr)
        elif o == '-c':
            optiondict['isgrayordinate'] = True
            print('Input fMRI file is a converted CIFTI file')
        elif o == '--AR':
            optiondict['armodelorder'] = int(a)
            if optiondict['armodelorder'] < 1:
                print('AR model order must be an integer greater than 0')
                sys.exit()
            linkchar = '='
            print('AR model order set to ', optiondict['armodelorder'])
        elif o == '-O':
            optiondict['oversampfactor'] = int(a)
            if optiondict['oversampfactor'] < 1:
                print('oversampling factor must be an integer greater than or equal to 1')
                sys.exit()
            print('oversampling factor set to ', optiondict['oversampfactor'])
        elif o == '--ica':
            optiondict['refinetype'] = 'ica'
            print('Will use ICA procedure to refine regressor rather than simple averaging')
        elif o == '--pca':
            optiondict['refinetype'] = 'pca'
            print('Will use PCA procedure to refine regressor rather than simple averaging')
        elif o == '--numskip':
            optiondict['preprocskip'] = int(a)
            linkchar = '='
            print('Setting preprocessing trs skipped to ', optiondict['preprocskip'])
        elif o == '--regressor':
            filename = a
            linkchar = '='
            print('Will use regressor file', a)
        elif o == '--regressorfreq':
            inputfreq = float(a)
            linkchar = '='
            print('Setting regressor sample frequency to ', inputfreq)
        elif o == '--regressorstart':
            inputstarttime = float(a)
            linkchar = '='
            print('Setting regressor start time to ', inputstarttime)
        elif o == '--sliceorder':
            optiondict['sliceorder'] = int(a)
            linkchar = '='
            print('Setting slice order to ', optiondict['sliceorder'])
        elif o == '--nodetrend':
            optiondict['dodetrend'] = False
            print('Disabling linear trend removal in regressor generation and correlation preparation')
        elif o == '--refineupperlag':
            optiondict['lagmaskside'] = 'upper'
            print('Will only use lags between ', optiondict['lagminthresh'], ' and ', optiondict['lagmaxthresh'],
                  ' in refinement')
        elif o == '--refinelowerlag':
            optiondict['lagmaskside'] = 'lower'
            print('Will only use lags between ', -optiondict['lagminthresh'], ' and ', -optiondict['lagmaxthresh'],
                  ' in refinement')
        elif o == '--nogaussrefine':
            optiondict['gaussrefine'] = False
            print('Will not use gaussian correlation peak refinement')
        elif o == '--fastgauss':
            optiondict['fastgauss'] = True
            print('Will use alternative fast gauss refinement (does not work well)')
        elif o == '--refineoffset':
            optiondict['refineoffset'] = True
            print('Will refine offset time during subsequent passes')
        elif o == '--lagminthresh':
            optiondict['lagminthresh'] = float(a)
            optiondict['dorefineregressor'] = True
            linkchar = '='
            print('Using lagminthresh of ', optiondict['lagminthresh'])
        elif o == '--lagmaxthresh':
            optiondict['lagmaxthresh'] = float(a)
            optiondict['dorefineregressor'] = True
            linkchar = '='
            print('Using lagmaxthresh of ', optiondict['lagmaxthresh'])
        elif o == '--ampthresh':
            optiondict['ampthresh'] = float(a)
            optiondict['ampthreshfromsig'] = False
            optiondict['dorefineregressor'] = True
            linkchar = '='
            print('Using ampthresh of ', optiondict['ampthresh'])
        elif o == '--sigmathresh':
            optiondict['sigmathresh'] = float(a)
            optiondict['dorefineregressor'] = True
            linkchar = '='
            print('Using widththresh of ', optiondict['sigmathresh'])
        elif o == '--excludemask':
            optiondict['excludemaskname'] = a
            linkchar = '='
            print('Voxels in ', optiondict['excludemaskname'], ' will not be used to define or refine regressors')
        elif o == '--includemask':
            optiondict['includemaskname'] = a
            linkchar = '='
            print('Only voxels in ', optiondict['includemaskname'], ' will be used to define or refine regressors')
        elif o == '--refineweighting':
            optiondict['refineweighting'] = a
            if (
                        optiondict['refineweighting'] != 'none') and (
                        optiondict['refineweighting'] != 'R') and (
                        optiondict['refineweighting'] != 'R2'):
                print('unsupported refinement weighting!')
                sys.exit()
            linkchar = '='
        elif o == '--tmask':
            optiondict['usetmask'] = True
            optiondict['tmaskname'] = a
            linkchar = '='
            print('Will multiply regressor by timecourse in ', optiondict['tmaskname'])
        elif o == '--refinepasses':
            optiondict['dorefineregressor'] = True
            optiondict['refinepasses'] = int(a)
            linkchar = '='
            print('Will do ', optiondict['refinepasses'], ' refinement passes')
        elif o in ('-h', '--help'):
            usage(optiondict['argstyle'])
            sys.exit()
        else:
            assert False, 'unhandled option'
        formattedcmdline.append('\t' + o + linkchar + a + ' \\')
    formattedcmdline[len(formattedcmdline) - 1] = formattedcmdline[len(formattedcmdline) - 1][:-2]

    timings.append(['Argument parsing done', time.time(), None, None])

    # write out the command used
    tide.writevec(formattedcmdline, outputname + '_formattedcommandline.txt')
    tide.writevec([' '.join(sys.argv)], outputname + '_commandline.txt')

    # open the fmri datafile
    nim, nim_data, nim_hdr, thedims, thesizes = tide.readfromnifti(fmrifilename)
    if nim_hdr['intent_code'] == 3002:
        print('input file is CIFTI')
        optiondict['isgrayordinate'] = True
        fileiscifti = True
        timepoints = nim_data.shape[4]
        numspatiallocs = nim_data.shape[5]
    else:
        print('input file is NIFTI')
        fileiscifti = False
        xsize, ysize, numslices, timepoints = tide.parseniftidims(thedims)
        numspatiallocs = int(xsize) * int(ysize) * int(numslices)

    # correct some fields if necessary
    if optiondict['isgrayordinate']:
        fmritr = 0.72  # this is wrong and is a hack until I can parse CIFTI XML
    else:
        if nim_hdr.get_xyzt_units()[1] == 'msec':
            fmritr = thesizes[4] / 1000.0
        else:
            fmritr = thesizes[4]
    if realtr > 0.0:
        fmritr = realtr
    oversamptr = fmritr / optiondict['oversampfactor']
    if optiondict['verbose']:
        print('fmri data: ', timepoints, ' timepoints, tr = ', fmritr, ', oversamptr =', oversamptr)
    print(numspatiallocs, ' spatial locations, ', timepoints, ' timepoints')
    xdim, ydim, slicethickness, tr = tide.parseniftisizes(thesizes)
    timings.append(['Finish reading fmrifile', time.time(), None, None])

    # if the user has specified start and stop points, limit check, then use these numbers
    validstart, validend = startendcheck(timepoints, optiondict['startpoint'], optiondict['endpoint'])
    if optiondict['dogaussianfilter']:
        print('applying gaussian spatial filter to timepoints ', validstart, ' to ', validend)
        for i in range(validstart, validend):
            tide.progressbar(i + 1, timepoints, label='Percent complete')
            nim_data[:, :, :, i] = tide.ssmooth(xdim, ydim, slicethickness, optiondict['gausssigma'],
                                                nim_data[:, :, :, i])
        timings.append(['End 3D smoothing', time.time(), None, None])

    # reshape the data and trim to a time range, if specified
    fmri_data = nim_data.reshape((numspatiallocs, timepoints))[:, validstart:validend + 1]
    timepoints = validend - validstart + 1

    # read in the optional masks
    internalincludemask = None
    internalexcludemask = None
    if optiondict['includemaskname'] is not None:
        nimincludemask, theincludemask, nimincludemask_hdr, theincludemaskdims, theincludmasksizes = tide.readfromnifti(
            optiondict['includemaskname'])
        if not tide.checkspacematch(theincludemaskdims, thedims):
            print('Dimensions of include mask do not match the fmri data - exiting')
            sys.exit()
        internalincludemask = theincludemask.reshape(numspatiallocs)
    if optiondict['excludemaskname'] is not None:
        nimexcludemask, theexcludemask, nimexcludemask_hdr, theexcludemaskdims, theexcludmasksizes = tide.readfromnifti(
            optiondict['excludemaskname'])
        theexcludemask = 1.0 - theexcludemask
        if not tide.checkspacematch(theexcludemaskdims, thedims):
            print('Dimensions of exclude mask do not match the fmri data - exiting')
            sys.exit()
        internalexcludemask = theexcludemask.reshape(numspatiallocs)

    # read in the timecourse to resample
    timings.append(['Start of reference prep', time.time(), None, None])
    if filename is None:
        print('no regressor file specified - will use the global mean regressor')
        optiondict['useglobalref'] = True

    if optiondict['useglobalref']:
        inputfreq = 1.0 / fmritr
        inputperiod = 1.0 * fmritr
        inputstarttime = 0.0
        inputvec = getglobalsignal(fmri_data, optiondict, includemask=internalincludemask,
                                   excludemask=internalexcludemask)
        optiondict['preprocskip'] = 0
    else:
        if inputfreq is None:
            print('no regressor frequency specified - defaulting to 1/tr')
            inputfreq = 1.0 / fmritr
        if inputstarttime is None:
            print('no regressor start time specified - defaulting to 0.0')
            inputstarttime = 0.0
        inputperiod = 1.0 / inputfreq
        inputvec = tide.readvec(filename)
    numreference = len(inputvec)
    print('regressor start time, end time, and step', inputstarttime, inputstarttime + numreference * inputperiod,
          inputperiod)

    if optiondict['verbose']:
        print('input vector length', len(inputvec), 'input freq', inputfreq, 'input start time', inputstarttime)

    # make numreference divisible by 4
    # numreference = numreference - numreference % 4
    # reference_x = np.r_[0.0:1.0 * numreference] / inputfreq - (inputstarttime + optiondict['offsettime'])
    reference_x = np.r_[0.0:numreference] * inputperiod - (inputstarttime + optiondict['offsettime'])

    # Print out initial information
    if optiondict['verbose']:
        print('there are ', numreference, ' points in the original regressor')
        print('the timepoint spacing is ', 1.0 / inputfreq)
        print('the input timecourse start time is ', inputstarttime)

    # generate the time axes
    fmrifreq = 1.0 / fmritr
    optiondict['fmrifreq'] = fmrifreq
    skiptime = fmritr * (optiondict['preprocskip'] + optiondict['addedskip'])
    print('first fMRI point is at ', skiptime, ' seconds relative to time origin')
    initial_fmri_x = np.r_[0.0:(timepoints - optiondict['addedskip'])] * fmritr + skiptime
    os_fmri_x = np.r_[0.0:(timepoints - optiondict['addedskip']) * optiondict['oversampfactor'] - (
        optiondict['oversampfactor'] - 1)] * oversamptr + skiptime
    if optiondict['verbose']:
        print(len(os_fmri_x))
        print(len(initial_fmri_x))

    # Clip the data
    if not optiondict['useglobalref'] and False:
        clipstart = bisect.bisect_left(reference_x, os_fmri_x[0] - 2.0 * optiondict['lagmin'])
        clipend = bisect.bisect_left(reference_x, os_fmri_x[-1] + 2.0 * optiondict['lagmax'])
        print('clip indices=', clipstart, clipend, reference_x[clipstart], reference_x[clipend], os_fmri_x[0],
              os_fmri_x[-1])

    # now correct for the offset into the fMRI timecourse caused by skipping initial points.  NOT TESTED - 11/18/13
    # reference_x=reference_x-skiptime

    # generate the comparison regressor from the input timecourse
    # correct the output time points
    # check for extrapolation
    if os_fmri_x[0] < reference_x[0]:
        print('WARNING: extrapolating ', os_fmri_x[0] - reference_x[0], ' seconds of data at beginning of timecourse')
    if os_fmri_x[-1] > reference_x[-1]:
        print('WARNING: extrapolating ', os_fmri_x[-1] - reference_x[-1], ' seconds of data at end of timecourse')
    ##########################
    # invert the regressor if necessary
    if optiondict['invertregressor']:
        invertfac = -1.0
    else:
        invertfac = 1.0

    if optiondict['dodetrend']:
        reference_y = invertfac * tide.detrend(inputvec[0:numreference], demean=optiondict['dodemean'])
    else:
        reference_y = invertfac * (inputvec[0:numreference] - np.mean(inputvec[0:numreference]))

    # write out the reference regressor prior to filtering
    tide.writenpvecs(reference_y, outputname + '_reference_origres_prefilt.txt')

    # band limit the regressor if that is needed
    print('filtering to ', theprefilter.gettype(), ' band')
    reference_y_classfilter = theprefilter.apply(inputfreq, reference_y)
    reference_y = reference_y_classfilter

    # write out the reference regressor used
    tide.writenpvecs(tide.stdnormalize(reference_y), outputname + '_reference_origres.txt')

    # filter the input data for antialiasing and to separate physiological components
    if optiondict['antialias']:
        if optiondict['zpfilter']:
            print('applying zero phase antialiasing filter')
            if optiondict['verbose']:
                print('    input freq:', inputfreq)
                print('    fmri freq:', fmrifreq)
                print('    npoints:', len(reference_y))
                print('    filtorder:', optiondict['filtorder'])
            print(inputfreq, fmrifreq, optiondict['filtorder'])  # debug
            reference_y_filt = tide.dolpfiltfilt(inputfreq, 0.5 * fmrifreq, reference_y, optiondict['filtorder'],
                                                 padlen=int(inputfreq * optiondict['padseconds']))
        else:
            if optiondict['trapezoidalfftfilter']:
                print('applying trapezoidal antialiasing filter')
                reference_y_filt = tide.dolptrapfftfilt(inputfreq, 0.25 * fmrifreq, 0.5 * fmrifreq, reference_y,
                                                        padlen=int(inputfreq * optiondict['padseconds']))
            else:
                print('applying brickwall antialiasing filter')
                reference_y_filt = tide.dolpfftfilt(inputfreq, 0.5 * fmrifreq, reference_y,
                                                    padlen=int(inputfreq * optiondict['padseconds']))
        reference_y = reference_y_filt.real

    warnings.filterwarnings('ignore', 'Casting*')

    if optiondict['fakerun']:
        sys.exit()

    # prepare the temporal mask
    if optiondict['usetmask']:
        tmask_y = maketmask(optiondict['tmaskname'], reference_x, 0.0 * reference_y)
        tmaskos_y = tide.doresample(reference_x, tmask_y, os_fmri_x, method=optiondict['interptype'])
        tide.writenpvecs(tmask_y, outputname + '_temporalmask.txt')

    # write out the resampled reference regressors
    if optiondict['dodetrend']:
        resampnonosref_y = tide.detrend(
            tide.doresample(reference_x, reference_y, initial_fmri_x, method=optiondict['interptype']),
            demean=optiondict['dodemean'])
        resampref_y = tide.detrend(
            tide.doresample(reference_x, reference_y, os_fmri_x, method=optiondict['interptype']),
            demean=optiondict['dodemean'])
    else:
        resampnonosref_y = tide.doresample(reference_x, reference_y, initial_fmri_x, method=optiondict['interptype'])
        resampref_y = tide.doresample(reference_x, reference_y, os_fmri_x, method=optiondict['interptype'])

    if optiondict['refinepasses'] > 1:
        nonosrefname = '_reference_fmrires_pass1.txt'
        osrefname = '_reference_resampres_pass1.txt'
    else:
        nonosrefname = '_reference_fmrires.txt'
        osrefname = '_reference_resampres.txt'

    if optiondict['usetmask']:
        resampnonosref_y *= tmask_y
        thefit, R = tide.mlregress(tmask_y, resampnonosref_y)
        resampnonosref_y -= thefit[0, 1] * tmask_y
        resampref_y *= tmaskos_y
        thefit, R = tide.mlregress(tmaskos_y, resampref_y)
        resampref_y -= thefit[0, 1] * tmaskos_y

    tide.writenpvecs(tide.stdnormalize(resampnonosref_y), outputname + nonosrefname)
    tide.writenpvecs(tide.stdnormalize(resampref_y), outputname + osrefname)
    timings.append(['End of reference prep', time.time(), None, None])

    corrtr = oversamptr
    if optiondict['verbose']:
        print('corrtr=', corrtr)

    if optiondict['gccphat']:
        numccorrlags = optiondict['oversampfactor'] * (timepoints - optiondict['addedskip'])
    else:
        numccorrlags = 2 * optiondict['oversampfactor'] * (timepoints - optiondict['addedskip']) - 1
    # Offset by -tr/2 11/5/15 to remove a systematic bias in the lag times
    # Realized 12/11/15 from simulation that this is actually a mistake. The real expression is more complicated.
    # Fixed and tested.  Lagtime is now estimated without bias at all oversample factors (and oversampling doesn't actually
    #     seem to contribute any increase in accuracy
    corrscale = np.r_[0.0:numccorrlags] * corrtr - (numccorrlags * corrtr) / 2.0 + (optiondict[
                                                                                        'oversampfactor'] - 0.5) * corrtr

    corrorigin = numccorrlags // 2 + 1
    lagmininpts = int((-optiondict['lagmin'] / corrtr) - 0.5)
    lagmaxinpts = int((optiondict['lagmax'] / corrtr) + 0.5)
    if optiondict['verbose']:
        print('corrorigin at point ', corrorigin, corrscale[corrorigin])
        print('corr range from ', corrorigin - lagmininpts, '(', corrscale[
            corrorigin - lagmininpts], ') to ', corrorigin + lagmaxinpts, '(', corrscale[corrorigin + lagmaxinpts], ')')

    if optiondict['savecorrtimes']:
        tide.writenpvecs(corrscale[corrorigin - lagmininpts:corrorigin + lagmaxinpts], outputname + '_corrtimes.txt')

    # allocate all of the data arrays
    if fileiscifti:
        nativespaceshape = (1, 1, 1, 1, numspatiallocs)
        nativearmodelshape = (1, 1, 1, optiondict['armodelorder'], numspatiallocs)
    else:
        nativespaceshape = (xsize, ysize, numslices)
        nativearmodelshape = (xsize, ysize, numslices, optiondict['armodelorder'])
    internalspaceshape = numspatiallocs
    internalarmodelshape = (numspatiallocs, optiondict['armodelorder'])
    meanval = np.zeros(internalspaceshape)
    lagtimes = np.zeros(internalspaceshape)
    lagstrengths = np.zeros(internalspaceshape)
    lagsigma = np.zeros(internalspaceshape)
    lagmask = np.zeros(internalspaceshape)
    corrmask = np.zeros(internalspaceshape)
    R2 = np.zeros(internalspaceshape)

    corroutlen = len(corrscale[corrorigin - lagmininpts:corrorigin + lagmaxinpts])
    if fileiscifti:
        nativecorrshape = (1, 1, 1, corroutlen, numspatiallocs)
    else:
        nativecorrshape = (xsize, ysize, numslices, corroutlen)
    internalcorrshape = (numspatiallocs, corroutlen)
    corrout = np.zeros(internalcorrshape)
    gaussout = np.zeros(internalcorrshape)

    if fileiscifti:
        nativefmrishape = (1, 1, 1, len(initial_fmri_x), numspatiallocs)
    else:
        nativefmrishape = (xsize, ysize, numslices, len(initial_fmri_x))
    internalfmrishape = (numspatiallocs, len(initial_fmri_x))
    lagtc = np.zeros(internalfmrishape)

    if optiondict['dorefineregressor']:
        shiftedtcs = np.zeros(internalfmrishape)
        refinemask = np.zeros(internalspaceshape, dtype='int16')

    if optiondict['doglmfilt'] or optiondict['doprewhiten']:
        meanvalue = np.zeros(internalspaceshape)
        rvalue = np.zeros(internalspaceshape)
        r2value = np.zeros(internalspaceshape)
        rCBV = np.zeros(internalspaceshape)
        fitcoff = np.zeros(internalspaceshape)
        datatoremove = np.zeros(internalfmrishape)
        filtereddata = np.zeros(internalfmrishape)
        prewhiteneddata = np.zeros(internalfmrishape)
        arcoffs = np.zeros(internalarmodelshape)

    # prepare for fast resampling
    padvalue = max((-optiondict['lagmin'], optiondict['lagmax'])) + 30.0
    # print('setting up fast resampling with padvalue =',padvalue)
    upsampleratio = 100.0
    numpadtrs = int(padvalue / fmritr)
    padvalue = fmritr * numpadtrs
    genlagtc = tide.fastresampler(reference_x, reference_y, padvalue=padvalue)

    # find the threshold value for the image data
    threshval = tide.getfracval(fmri_data[:, optiondict['addedskip']], 0.98) / 25.0
    if optiondict['verbose']:
        print('image threshval =', threshval)

    # cycle over all voxels
    refine = True
    if optiondict['verbose']:
        print('refine is set to ', refine)
    optiondict['edgebufferfrac'] = max([optiondict['edgebufferfrac'], 2.0 / len(corrscale)])
    if optiondict['verbose']:
        print('edgebufferfrac set to ', optiondict['edgebufferfrac'])

    for thepass in range(1, optiondict['refinepasses'] + 1):
        # initialize the pass
        if optiondict['dorefineregressor']:
            print('\n\n*********************')
            print('Pass number ', thepass)

        referencetc = tide.corrnormalize(resampref_y, optiondict['usewindowfunc'], optiondict['dodetrend'])

        # Step 0 - estimate significance
        if optiondict['estimate_significance']:
            timings.append(['Significance estimation start, pass ' + str(thepass), time.time(), None, None])
            print('\n\nSignificance estimation, pass ' + str(thepass))
            oversampfreq = optiondict['oversampfactor'] / fmritr
            if optiondict['verbose']:
                print('calling getNullDistributionData with args:', oversampfreq, fmritr, corrorigin, lagmininpts,
                      lagmaxinpts)
            corrdistdata = getNullDistributionData(referencetc, corrscale, theprefilter,
                                                   oversampfreq, corrorigin, lagmininpts, lagmaxinpts,
                                                   optiondict)

            # calculate percentiles for the crosscorrelation from the distribution data
            optiondict['sighistlen'] = 100
            thepercentiles = [0.95, 0.99, 0.995, 0.999]
            thepvalnames = []
            for thispercentile in thepercentiles:
                thepvalnames.append(str(1.0 - thispercentile).replace('.', 'p'))

            pcts, pcts_fit = tide.sigFromDistributionData(corrdistdata, optiondict['sighistlen'],
                                                          thepercentiles, nozero=optiondict['nohistzero'])
            if optiondict['ampthreshfromsig']:
                print('setting ampthresh to the p<', 1.0 - thepercentiles[0], ' threshhold')
                optiondict['ampthresh'] = pcts[2]
            tide.printthresholds(pcts, thepercentiles, 'Crosscorrelation significance thresholds from data:')
            tide.makeandsavehistogram(corrdistdata, optiondict['sighistlen'], 0,
                                      outputname + '_nullcorrelationhist_pass' + str(thepass),
                                      displaytitle='Null correlation histogram, pass' + str(thepass),
                                      displayplots=optiondict['displayplots'], refine=False)
            timings.append(['Significance estimation end, pass ' + str(thepass), time.time(), optiondict['numestreps'],
                            'repetitions'])

        # Step 1 - time lag estimation
        print('\n\nTime lag estimation, pass ' + str(thepass))
        timings.append(['Time lag estimation start, pass ' + str(thepass), time.time(), None, None])
        voxelsprocessed_cp = correlationpass(fmri_data[:, optiondict['addedskip']:], referencetc,
                                             initial_fmri_x, os_fmri_x,
                                             fmritr,
                                             corrorigin, lagmininpts, lagmaxinpts,
                                             corrmask, corrout, meanval,
                                             theprefilter,
                                             optiondict)
        timings.append(['Time lag estimation end, pass ' + str(thepass), time.time(), voxelsprocessed_cp, 'voxels'])

        # Step 2 - correlation fitting
        print('\n\nCorrelation fitting, pass ' + str(thepass))
        timings.append(['Correlation fitting start, pass ' + str(thepass), time.time(), None, None])

        voxelsprocessed_fc = fitcorr(genlagtc, initial_fmri_x,
                                     lagtc, fmritr,
                                     threshval, corrscale[corrorigin - lagmininpts:corrorigin + lagmaxinpts],
                                     corrmask, lagmask, lagtimes, lagstrengths, lagsigma, corrout, meanval, gaussout,
                                     R2,
                                     optiondict)
        timings.append(['Correlation fitting end, pass ' + str(thepass), time.time(), voxelsprocessed_fc, 'voxels'])

        # Step 3 - regressor refinement for next pass
        if optiondict['dorefineregressor'] and thepass < optiondict['refinepasses']:
            print('\n\nRegressor refinement, pass' + str(thepass))
            timings.append(['Regressor refinement start, pass ' + str(thepass), time.time(), None, None])
            if optiondict['refineoffset']:
                peaklag, peakheight, peakwidth = tide.gethistprops(lagtimes[np.where(lagmask > 0)],
                                                                   optiondict['histlen'])
                optiondict['offsettime'] = peaklag
                optiondict['offsettime_total'] += peaklag
                print('offset time set to ', optiondict['offsettime'], ', total is ', optiondict['offsettime_total'])

            # regenerate regressor for next pass
            voxelsprocessed_rr, outputdata = refineregressor(
                fmri_data[:, :], fmritr, shiftedtcs, refinemask,
                lagstrengths, lagtimes, lagsigma, R2, theprefilter, optiondict, includemask=internalincludemask,
                excludemask=internalexcludemask)
            normoutputdata = tide.stdnormalize(theprefilter.apply(fmrifreq, outputdata))
            tide.writenpvecs(normoutputdata, outputname + '_refinedregressor_pass' + str(thepass) + '.txt')

            if optiondict['dodetrend']:
                resampnonosref_y = tide.detrend(tide.doresample(initial_fmri_x, normoutputdata, initial_fmri_x,
                                                                method=optiondict['interptype']),
                                                demean=optiondict['dodemean'])
                resampref_y = tide.detrend(tide.doresample(initial_fmri_x, normoutputdata, os_fmri_x,
                                                           method=optiondict['interptype']),
                                           demean=optiondict['dodemean'])
            else:
                resampnonosref_y = tide.doresample(initial_fmri_x, normoutputdata, initial_fmri_x,
                                                   method=optiondict['interptype'])
                resampref_y = tide.doresample(initial_fmri_x, normoutputdata, os_fmri_x,
                                              method=optiondict['interptype'])
            if optiondict['usetmask']:
                resampnonosref_y *= tmask_y
                thefit, R = tide.mlregress(tmask_y, resampnonosref_y)
                resampnonosref_y -= thefit[0, 1] * tmask_y
                resampref_y *= tmaskos_y
                thefit, R = tide.mlregress(tmaskos_y, resampref_y)
                resampref_y -= thefit[0, 1] * tmaskos_y

            # reinitialize lagtc for resampling
            genlagtc = tide.fastresampler(initial_fmri_x, normoutputdata, padvalue=padvalue)
            nonosrefname = '_reference_fmrires_pass' + str(thepass + 1) + '.txt'
            osrefname = '_reference_resampres_pass' + str(thepass + 1) + '.txt'
            tide.writenpvecs(tide.stdnormalize(resampnonosref_y), outputname + nonosrefname)
            tide.writenpvecs(tide.stdnormalize(resampref_y), outputname + osrefname)
            timings.append(
                ['Regressor refinement end, pass ' + str(thepass), time.time(), voxelsprocessed_rr, 'voxels'])

    # Post refinement step 1 - GLM fitting to remove moving signal
    if optiondict['doglmfilt'] or optiondict['doprewhiten']:
        timings.append(['GLM filtering start, pass ' + str(thepass), time.time(), None, None])
        if optiondict['doglmfilt']:
            print('\n\nGLM filtering')
        if optiondict['doprewhiten']:
            print('\n\nPrewhitening')
        reportstep = 1000
        for vox in range(0, numspatiallocs):
            if vox % reportstep == 0 or vox == numspatiallocs - 1:
                tide.progressbar(vox + 1, numspatiallocs, label='Percent complete')
            inittc = 1.0 * (fmri_data[vox, optiondict['addedskip']:])
            if np.mean(inittc) >= threshval:
                # slope, intercept , R, pval, thestderr = scipy.linregress(lagtc[vox, :], inittc)
                thefit, R = tide.mlregress(lagtc[vox, :], inittc)
                meanvalue[vox] = thefit[0, 0]
                rvalue[vox] = R
                r2value[vox] = R * R
                fitcoff[vox] = thefit[0, 1]
                rCBV[vox] = thefit[0, 1] / thefit[0, 0]
                datatoremove[vox, :] = fitcoff[vox] * lagtc[vox, :]
                thefilttc = inittc - datatoremove[vox, :]
                filtereddata[vox, :] = thefilttc
                if optiondict['doprewhiten']:
                    arcoffs[vox, :] = pacf_yw(thefilttc, nlags=optiondict['armodelorder'])[1:]
                    prewhiteneddata[vox, :] = prewhiten(inittc, arcoffs[vox, :])
        if optiondict['doprewhiten']:
            arcoff_ref = pacf_yw(resampref_y, nlags=optiondict['armodelorder'])[1:]
            print('\nAR coefficient(s) for reference waveform: ', arcoff_ref)
            resampref_y_pw = prewhiten(resampref_y, arcoff_ref)
        else:
            resampref_y_pw = 1.0 * resampref_y
        if optiondict['usewindowfunc']:
            if optiondict['gccphat']:
                referencetc_pw = tide.hamming(len(resampref_y_pw)) * tide.detrend(
                    tide.stdnormalize(resampref_y_pw)) / len(resampref_y_pw)
            else:
                referencetc_pw = tide.stdnormalize(
                    tide.hamming(len(resampref_y_pw)) * tide.detrend(tide.stdnormalize(resampref_y_pw))) / len(
                    resampref_y_pw)
        else:
            if optiondict['gccphat']:
                referencetc_pw = tide.detrend(tide.stdnormalize(resampref_y_pw)) / len(resampref_y_pw)
            else:
                referencetc_pw = tide.stdnormalize(tide.detrend(tide.stdnormalize(resampref_y_pw))) / len(
                    resampref_y_pw)
        print('')
        if optiondict['displayplots']:
            fig = figure()
            ax = fig.add_subplot(111)
            ax.set_title('initial and prewhitened reference')
            plot(os_fmri_x, referencetc, os_fmri_x, referencetc_pw)

    # Post refinement step 2 - prewhitening
    if optiondict['doprewhiten']:
        print('Step 3 - reprocessing prewhitened data')
        timings.append(['Step 3 start', time.time(), None, None])
        correlationpass(prewhiteneddata, referencetc_pw,
                        initial_fmri_x, os_fmri_x,
                        fmritr,
                        corrorigin, lagmininpts, lagmaxinpts,
                        corrmask, corrout, meanval,
                        theprefilter,
                        optiondict)

    # Post refinement step 3 - make and save interesting histograms
    timings.append(['Start saving histograms', time.time(), None, None])
    tide.makeandsavehistogram(lagtimes[np.where(lagmask > 0)], optiondict['histlen'], 0, outputname + '_laghist',
                              displaytitle='lagtime histogram', displayplots=optiondict['displayplots'], refine=False)
    tide.makeandsavehistogram(lagstrengths[np.where(lagmask > 0)], optiondict['histlen'], 0,
                              outputname + '_strengthhist',
                              displaytitle='lagstrength histogram', displayplots=optiondict['displayplots'],
                              therange=(0.0, 1.0))
    tide.makeandsavehistogram(lagsigma[np.where(lagmask > 0)], optiondict['histlen'], 1, outputname + '_widthhist',
                              displaytitle='lagsigma histogram', displayplots=optiondict['displayplots'])
    if optiondict['doglmfilt']:
        tide.makeandsavehistogram(r2value[np.where(lagmask > 0)], optiondict['histlen'], 1, outputname + '_Rhist',
                                  displaytitle='correlation R2 histogram', displayplots=optiondict['displayplots'])

    # Post refinement step 4 - save out all of the important arrays to nifti files
    # write out the options used
    tide.writedict(optiondict, outputname + '_options.txt')

    if fileiscifti:
        outsuffix3d = '.dscalar'
        outsuffix4d = '.dtseries'
    else:
        outsuffix3d = ''
        outsuffix4d = ''

    # do ones with one time point first
    timings.append(['Start saving maps', time.time(), None, None])
    theheader = nim_hdr
    if fileiscifti:
        theheader['intent_code'] = 3006
    else:
        theheader['dim'][0] = 3
        theheader['dim'][4] = 1
    tide.savetonifti(lagtimes.reshape(nativespaceshape), theheader, thesizes, outputname + '_lagtimes' + outsuffix3d)
    tide.savetonifti(lagstrengths.reshape(nativespaceshape), theheader, thesizes,
                     outputname + '_lagstrengths' + outsuffix3d)
    tide.savetonifti(R2.reshape(nativespaceshape), theheader, thesizes, outputname + '_R2' + outsuffix3d)
    tide.savetonifti(lagsigma.reshape(nativespaceshape), theheader, thesizes, outputname + '_lagsigma' + outsuffix3d)
    tide.savetonifti(lagmask.reshape(nativespaceshape), theheader, thesizes, outputname + '_lagmask' + outsuffix3d)
    if optiondict['doglmfilt']:
        tide.savetonifti(rvalue.reshape(nativespaceshape), theheader, thesizes, outputname + '_fitR' + outsuffix3d)
        tide.savetonifti(r2value.reshape(nativespaceshape), theheader, thesizes, outputname + '_fitR2' + outsuffix3d)
        tide.savetonifti(meanvalue.reshape(nativespaceshape), theheader, thesizes, outputname + '_mean' + outsuffix3d)
        tide.savetonifti(fitcoff.reshape(nativespaceshape), theheader, thesizes, outputname + '_fitcoff' + outsuffix3d)
        tide.savetonifti(rCBV.reshape(nativespaceshape), theheader, thesizes, outputname + '_rCBV' + outsuffix3d)
    if optiondict['estimate_significance']:
        for i in range(0, len(thepercentiles)):
            pmask = np.where(lagstrengths > pcts[i], lagmask, 0 * lagmask)
            tide.writenpvecs(np.array([pcts[i]]), outputname + '_p_lt_' + thepvalnames[i] + '_thresh.txt')
            tide.savetonifti(pmask.reshape(nativespaceshape), theheader, thesizes,
                             outputname + '_p_lt_' + thepvalnames[i] + '_mask' + outsuffix3d)

    # now do the ones with other numbers of time points
    theheader = nim_hdr
    if fileiscifti:
        theheader['intent_code'] = 3002
    else:
        theheader['dim'][4] = len(corrscale)
    theheader['toffset'] = corrscale[corrorigin - lagmininpts]
    theheader['pixdim'][4] = corrtr
    tide.savetonifti(gaussout.reshape(nativecorrshape), theheader, thesizes, outputname + '_gaussout' + outsuffix4d)
    tide.savetonifti(corrout.reshape(nativecorrshape), theheader, thesizes, outputname + '_corrout' + outsuffix4d)
    theheader['toffset'] = 0.0
    if optiondict['saveprewhiten']:
        theheader = nim.header
        if fileiscifti:
            theheader['intent_code'] = 3002
        else:
            theheader['dim'][4] = optiondict['armodelorder']
        tide.savetonifti(arcoffs.reshape(nativearmodelshape), theheader, thesizes, outputname + '_arN' + outsuffix4d)

    theheader = nim_hdr
    if fileiscifti:
        theheader['intent_code'] = 3002
    else:
        theheader['dim'][4] = len(initial_fmri_x)
    if optiondict['savelagregressors']:
        tide.savetonifti(lagtc.reshape(nativefmrishape), theheader, thesizes,
                         outputname + '_lagregressor' + outsuffix4d)
    if optiondict['dorefineregressor']:
        tide.savetonifti(shiftedtcs.reshape(nativefmrishape), theheader, thesizes,
                         outputname + '_shiftedtcs' + outsuffix4d)
        tide.savetonifti(refinemask.reshape(nativespaceshape), theheader, thesizes,
                         outputname + '_refinemask' + outsuffix3d)
    if optiondict['doglmfilt'] and optiondict['saveglmfiltered']:
        tide.savetonifti(datatoremove.reshape(nativefmrishape), theheader, thesizes,
                         outputname + '_datatoremove' + outsuffix4d)
        tide.savetonifti(filtereddata.reshape(nativefmrishape), theheader, thesizes,
                         outputname + '_filtereddata' + outsuffix4d)
    if optiondict['saveprewhiten']:
        tide.savetonifti(prewhiteneddata.reshape(nativefmrishape), theheader, thesizes,
                         outputname + '_prewhiteneddata' + outsuffix4d)
    print('done')

    if optiondict['displayplots']:
        show()
    timings.append(['Done', time.time(), None, None])

    # Post refinement step 5 - process and save timing information
    nodeline = 'Processed on ' + platform.node()
    tide.proctiminginfo(timings, outputfile=outputname + '_runtimings.txt', extraheader=nodeline)


if __name__ == '__main__':
    main()