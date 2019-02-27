# /usr/bin/env python
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
# $Author: frederic $
# $Date: 2016/07/12 13:50:29 $
# $Id: tide_funcs.py,v 1.4 2016/07/12 13:50:29 frederic Exp $
#
from __future__ import print_function, division

import numpy as np
import sys
import os
import pandas as pd
import json

# ---------------------------------------- Global constants -------------------------------------------
MAXLINES = 10000000

# ----------------------------------------- Conditional imports ---------------------------------------
try:
    import nibabel as nib

    nibabelexists = True
except ImportError:
    nibabelexists = False

# ---------------------------------------- NIFTI file manipulation ---------------------------
if nibabelexists:

    def readfromnifti(inputfile):
        r"""Open a nifti file and read in the various important parts

        Parameters
        ----------
        inputfile : str
            The name of the nifti file.

        Returns
        -------
        nim : nifti image structure
        nim_data : array-like
        nim_hdr : nifti header
        thedims : int array
        thesizes : float array

        """
        if os.path.isfile(inputfile):
            inputfilename = inputfile
        elif os.path.isfile(inputfile + ".nii.gz"):
            inputfilename = inputfile + ".nii.gz"
        elif os.path.isfile(inputfile + ".nii"):
            inputfilename = inputfile + ".nii"
        else:
            print("nifti file", inputfile, "does not exist")
            sys.exit()
        nim = nib.load(inputfilename)
        nim_data = nim.get_data()
        nim_hdr = nim.get_header()
        thedims = nim_hdr["dim"].copy()
        thesizes = nim_hdr["pixdim"].copy()
        return nim, nim_data, nim_hdr, thedims, thesizes

    # dims are the array dimensions along each axis
    def parseniftidims(thedims):
        r"""Split the dims array into individual elements

        Parameters
        ----------
        thedims : int array
            The nifti dims structure

        Returns
        -------
        nx, ny, nz, nt : int
            Number of points along each dimension
        """
        return thedims[1], thedims[2], thedims[3], thedims[4]

    # sizes are the mapping between voxels and physical coordinates
    def parseniftisizes(thesizes):
        r"""Split the size array into individual elements

        Parameters
        ----------
        thesizes : float array
            The nifti voxel size structure

        Returns
        -------
        dimx, dimy, dimz, dimt : float
            Scaling from voxel number to physical coordinates
        """
        return thesizes[1], thesizes[2], thesizes[3], thesizes[4]

    def savetonifti(thearray, theheader, thepixdim, thename):
        r""" Save a data array out to a nifti file

        Parameters
        ----------
        thearray : array-like
            The data array to save.
        theheader : nifti header
            A valid nifti header
        thepixdim : array
            The pixel dimensions.
        thename : str
            The name of the nifti file to save

        Returns
        -------

        """
        outputaffine = theheader.get_best_affine()
        qaffine, qcode = theheader.get_qform(coded=True)
        saffine, scode = theheader.get_sform(coded=True)
        if theheader["magic"] == "n+2":
            output_nifti = nib.Nifti2Image(thearray, outputaffine, header=theheader)
            suffix = ".nii"
        else:
            output_nifti = nib.Nifti1Image(thearray, outputaffine, header=theheader)
            suffix = ".nii.gz"
        output_nifti.set_qform(qaffine, code=int(qcode))
        output_nifti.set_sform(saffine, code=int(scode))
        thedtype = thearray.dtype
        if thedtype == np.uint8:
            theheader.datatype = 2
        elif thedtype == np.int16:
            theheader.datatype = 4
        elif thedtype == np.int32:
            theheader.datatype = 8
        elif thedtype == np.float32:
            theheader.datatype = 16
        elif thedtype == np.complex64:
            theheader.datatype = 32
        elif thedtype == np.float64:
            theheader.datatype = 64
        elif thedtype == np.int8:
            theheader.datatype = 256
        elif thedtype == np.uint16:
            theheader.datatype = 512
        elif thedtype == np.uint32:
            theheader.datatype = 768
        elif thedtype == np.int64:
            theheader.datatype = 1024
        elif thedtype == np.uint64:
            theheader.datatype = 1280
        elif thedtype == np.float128:
            theheader.datatype = 1536
        elif thedtype == np.complex128:
            theheader.datatype = 1792
        elif thedtype == np.complex256:
            theheader.datatype = 2048
        else:
            print("type", thedtype, "is not legal")
            sys.exit()

        output_nifti.to_filename(thename + suffix)
        output_nifti = None

    def checkifnifti(filename):
        r"""Check to see if a file name is a valid nifti name.

        Parameters
        ----------
        filename : str
            The file name

        Returns
        -------
        isnifti : bool
            True if name is a valid nifti file name.

        """
        if filename.endswith(".nii") or filename.endswith(".nii.gz"):
            return True
        else:
            return False

    def checkiftext(filename):
        r"""Check to see if the specified filename ends in '.txt'

        Parameters
        ----------
        filename : str
            The file name

        Returns
        -------
        istext : bool
            True if filename ends with '.txt'

        """
        if filename.endswith(".txt"):
            return True
        else:
            return False

    def getniftiroot(filename):
        r"""Strip a nifti filename down to the root with no extensions

        Parameters
        ----------
        filename : str
            The file name to strip

        Returns
        -------
        strippedname : str
            The file name without any nifti extensions

        """
        if filename.endswith(".nii"):
            return filename[:-4]
        elif filename.endswith(".nii.gz"):
            return filename[:-7]
        else:
            return filename

    def fmritimeinfo(niftifilename):
        r"""Retrieve the repetition time and number of timepoints from a nifti file

        Parameters
        ----------
        niftifilename : str
            The name of the nifti file

        Returns
        -------
        tr : float
            The repetition time, in seconds
        timepoints : int
            The number of points along the time axis

        """
        nim = nib.load(niftifilename)
        hdr = nim.get_header()
        thedims = hdr["dim"]
        thesizes = hdr["pixdim"]
        if hdr.get_xyzt_units()[1] == "msec":
            tr = thesizes[4] / 1000.0
        else:
            tr = thesizes[4]
        timepoints = thedims[4]
        return tr, timepoints

    def checkspacematch(hdr1, hdr2):
        r"""Check the headers of two nifti files to determine if the cover the same volume at the same resolution

        Parameters
        ----------
        hdr1 : nifti header structure
            The header of the first file
        hdr2 : nifti header structure
            The header of the second file

        Returns
        -------
        ismatched : bool
            True if the spatial dimensions and resolutions of the two files match.

        """
        dimmatch = checkspaceresmatch(hdr1["pixdim"], hdr2["pixdim"])
        resmatch = checkspacedimmatch(hdr1["dim"], hdr2["dim"])
        return dimmatch and resmatch

    def checkspaceresmatch(sizes1, sizes2):
        r"""Check the spatial pixdims of two nifti files to determine if they have the same resolution

        Parameters
        ----------
        sizes1 : float array
            The size array from the first nifti file 
        sizes2 : float array
            The size array from the second nifti file 

        Returns
        -------
        ismatched : bool
            True if the spatial resolutions of the two files match.

        """
        for i in range(1, 4):
            if sizes1[i] != sizes2[i]:
                print("File spatial resolutions do not match")
                print("sizeension ", i, ":", sizes1[i], "!=", sizes2[i])
                return False
            else:
                return True

    def checkspacedimmatch(dims1, dims2):
        r"""Check the dimension arrays of two nifti files to determine if the cover the same number of voxels in each dimension

        Parameters
        ----------
        dims1 : int array
            The dimension array from the first nifti file 
        dims2 : int array
            The dimension array from the second nifti file 

        Returns
        -------
        ismatched : bool
            True if the spatial dimensions of the two files match.
        """
        for i in range(1, 4):
            if dims1[i] != dims2[i]:
                print("File spatial voxels do not match")
                print("dimension ", i, ":", dims1[i], "!=", dims2[i])
                return False
            else:
                return True

    def checktimematch(dims1, dims2, numskip1=0, numskip2=0):
        r"""Check the dimensions of two nifti files to determine if the cover the same number of timepoints

        Parameters
        ----------
        dims1 : int array
            The dimension array from the first nifti file 
        dims2 : int array
            The dimension array from the second nifti file 
        numskip1 : int, optional
            Number of timepoints skipped at the beginning of file 1
        numskip2 : int, optional
            Number of timepoints skipped at the beginning of file 2

        Returns
        -------
        ismatched : bool
            True if the time dimension of the two files match.

        """
        if (dims1[4] - numskip1) != (dims2[4] - numskip2):
            print("File numbers of timepoints do not match")
            print(
                "dimension ",
                4,
                ":",
                dims1[4],
                "(skip ",
                numskip1,
                ") !=",
                dims2[4],
                " (skip ",
                numskip2,
                ")",
            )
            return False
        else:
            return True


# --------------------------- non-NIFTI file I/O functions ------------------------------------------
def checkifparfile(filename):
    r"""Checks to see if a file is an FSL style motion parameter file

    Parameters
    ----------
    filename : str
        The name of the file in question.

    Returns
    -------
    isparfile : bool
        True if filename ends in '.par', False otherwise.

    """
    if filename.endswith(".par"):
        return True
    else:
        return False


def readparfile(filename):
    r"""Checks to see if a file is an FSL style motion parameter file

    Parameters
    ----------
    filename : str
        The name of the file in question.

    Returns
    -------
    motiondict: dict
        All the timecourses in the file, keyed by name

    """
    labels = ["X", "Y", "Z", "RotX", "RotY", "RotZ"]
    motiontimeseries = readvecs(filename)
    motiondict = {}
    for j in range(0, 6):
        motiondict[labels[j]] = 1.0 * motiontimeseries[j, :]
    return motiondict


def readmotion(filename, colspec=None):
    r"""Reads motion regressors from filename (from the columns specified in colspec, if given)

    Parameters
    ----------
    filename : str
        The name of the file in question.
    colspec: str, optional
        The column numbers from the input file to use for the 6 motion regressors

    Returns
    -------
    motiondict: dict
        All the timecourses in the file, keyed by name

    """
    labels = ["X", "Y", "Z", "RotX", "RotY", "RotZ"]
    motiontimeseries = readvecs(filename, colspec=colspec)
    if motiontimeseries.shape[0] != 6:
        print(
            "readmotion: expect 6 motion regressors", motiontimeseries.shape[0], "given"
        )
        sys.exit()
    motiondict = {}
    for j in range(0, 6):
        motiondict[labels[j]] = 1.0 * motiontimeseries[j, :]
    return motiondict


def calcmotregressors(
    motiondict, start=0, end=-1, position=True, deriv=True, derivdelayed=False
):
    r"""Calculates various motion related timecourses from motion data dict, and returns an array

    Parameters
    ----------
    motiondict: dict
        A dictionary of the 6 motion direction vectors

    Returns
    -------
    motionregressors: array
        All the derivative timecourses to use in a numpy array

    """
    labels = ["X", "Y", "Z", "RotX", "RotY", "RotZ"]
    numpoints = len(motiondict[labels[0]])
    if end == -1:
        end = numpoints - 1
    if (0 <= start <= numpoints - 1) and (start < end + 1):
        numoutputpoints = end - start + 1

    numoutputregressors = 0
    if position:
        numoutputregressors += 6
    if deriv:
        numoutputregressors += 6
    if derivdelayed:
        numoutputregressors += 6
    if numoutputregressors > 0:
        outputregressors = np.zeros((numoutputregressors, numoutputpoints), dtype=float)
    else:
        print("no output types selected - exiting")
        sys.exit()
    activecolumn = 0
    if position:
        for thelabel in labels:
            outputregressors[activecolumn, :] = motiondict[thelabel][start : end + 1]
            activecolumn += 1
    if deriv:
        for thelabel in labels:
            outputregressors[activecolumn, 1:] = np.diff(
                motiondict[thelabel][start : end + 1]
            )
            activecolumn += 1
    if derivdelayed:
        for thelabel in labels:
            outputregressors[activecolumn, 2:] = np.diff(
                motiondict[thelabel][start : end + 1]
            )[1:]
            activecolumn += 1
    return outputregressors


def sliceinfo(slicetimes, tr):
    # find out what timepoints we have, and their spacing
    sortedtimes = np.sort(slicetimes)
    diffs = sortedtimes[1:] - sortedtimes[0:-1]
    minstep = np.max(diffs)
    numsteps = int(np.round(tr / minstep, 0))
    sliceoffsets = np.around(slicetimes / minstep).astype(np.int32) % numsteps
    return numsteps, minstep, sliceoffsets


def getslicetimesfromfile(slicetimename):
    filebase, extension = os.path.splitext(slicetimename)
    if extension == ".json":
        jsoninfodict = readdictfromjson(slicetimename)
        try:
            slicetimelist = jsoninfodict["SliceTiming"]
            slicetimes = np.zeros((len(slicetimelist)), dtype=np.float64)
            for idx, thetime in enumerate(slicetimelist):
                slicetimes[idx] = float(thetime)
        except KeyError:
            print(slicetimename, "is not a valid BIDS sidecar file")
            sys.exit()
    else:
        slicetimes = readvec(slicetimename)
    return slicetimes


def readbidssidecar(inputfilename):
    r"""Read key value pairs out of a BIDS sidecar file

    Parameters
    ----------
    inputfilename : str
        The name of the sidecar file (with extension)

    Returns
    -------
    thedict : dict
        The key value pairs from the json file

    """
    thefileroot, theext = os.path.splitext(inputfilename)
    if os.path.exists(thefileroot + ".json"):
        with open(thefileroot + ".json", "r") as json_data:
            d = json.load(json_data)
            return d
    else:
        print("sidecar file does not exist")
        return {}


def writedicttojson(thedict, thefilename):
    r"""Write key value pairs to a json file

    Parameters
    ----------
    thedict : dict
        The key value pairs from the json file
    thefilename : str
        The name of the json file (with extension)

    """
    with open(thefilename, "wb") as fp:
        fp.write(
            json.dumps(thedict, sort_keys=True, indent=4, separators=(",", ":")).encode(
                "utf-8"
            )
        )


def readdictfromjson(inputfilename):
    r"""Read key value pairs out of a json file

    Parameters
    ----------
    inputfilename : str
        The name of the json file (with extension)

    Returns
    -------
    thedict : dict
        The key value pairs from the json file

    """
    thefileroot, theext = os.path.splitext(inputfilename)
    if os.path.exists(thefileroot + ".json"):
        with open(thefileroot + ".json", "r") as json_data:
            d = json.load(json_data)
            return d
    else:
        print("specified json file does not exist")
        return {}


def readfmriprepconfounds(inputfilename):
    r"""Read time series out of an fmriprep confounds tsv file

    Parameters
    ----------
    inputfilename : str
        The root name of the tsv (no extension)

    Returns
    -------
        confounddict: dict
            All the timecourses in the file, keyed by the first row

    NOTE:  If file does not exist or is not valid, return an empty dictionary

    """
    confounddict = {}
    df = pd.read_csv(inputfilename + ".tsv", sep="\t", quotechar='"')
    for thecolname, theseries in df.iteritems():
        confounddict[thecolname] = theseries.values
    return confounddict


def readbidstsv(inputfilename):
    r"""Read time series out of a BIDS tsv file

    Parameters
    ----------
    inputfilename : str
        The root name of the tsv and accompanying json file (no extension)

    Returns
    -------
        samplerate : float
            Sample rate in Hz
        starttime : float
            Time of first point, in seconds
        columns : str array
            Names of the timecourses contained in the file
        data : 2D numpy array
            Timecourses from the file

    NOTE:  If file does not exist or is not valid, all return values are None

    """
    thefileroot, theext = os.path.splitext(inputfilename)
    if os.path.exists(thefileroot + ".json") and os.path.exists(
        thefileroot + ".tsv.gz"
    ):
        with open(thefileroot + ".json", "r") as json_data:
            d = json.load(json_data)
            try:
                samplerate = float(d["SamplingFrequency"])
            except:
                print("no samplerate found in json")
                return [None, None, None, None]
            try:
                starttime = float(d["StartTime"])
            except:
                print("no starttime found in json")
                return [None, None, None, None]
            try:
                columns = d["Columns"]
            except:
                print("no columns found in json")
                return [None, None, None, None]
        df = pd.read_csv(
            thefileroot + ".tsv.gz",
            compression="gzip",
            header=0,
            sep="\t",
            quotechar='"',
        )
        return samplerate, starttime, columns, np.transpose(df.as_matrix())
    else:
        print("file pair does not exist")
        return [None, None, None, None]


def readcolfrombidstsv(inputfilename, columnnum=0, columnname=None):
    r"""

    Parameters
    ----------
    inputfilename
    columnnum
    columnname

    Returns
    -------

    """
    samplerate, starttime, columns, data = readbidstsv(inputfilename)
    if data is None:
        print("no valid datafile found")
        return None, None, None
    else:
        if columnname is not None:
            # looking for a named column
            try:
                thecolnum = columns.index(columnname)
                return samplerate, starttime, data[thecolnum, :]
            except:
                print("no column named", columnname, "in", inputfilename)
                return None, None, None
        # we can only get here if columnname is undefined
        if not (0 < columnnum < len(columns)):
            print(
                "specified column number",
                columnnum,
                "is out of range in",
                inputfilename,
            )
            return None, None, None
        else:
            return samplerate, starttime, data[columnnum, :]


def colspectolist(colspec):
    collist = []
    theranges = colspec.split(",")

    def safeint(s):
        try:
            int(s)
            return int(s)
        except ValueError:
            print("COLSPECTOLIST:", s, "is not a legal integer - exiting")
            return None

    for thisrange in theranges:
        print("processing range", thisrange)
        theendpoints = thisrange.split("-")
        if len(theendpoints) == 1:
            collist.append(safeint(theendpoints[0]))
        elif len(theendpoints) == 2:
            start = safeint(theendpoints[0])
            end = safeint(theendpoints[1])
            if start < 0:
                print("COLSPECTOLIST:", start, "must be greater than zero")
                return None
            if end < start:
                print("COLSPECTOLIST:", end, "must be greater than or equal to", start)
                return None
            for i in range(start, end + 1):
                collist.append(i)
        else:
            print("COLSPECTOLIST: bad range specification - exiting")
            return None
    return sorted(collist)


def readvecs(inputfilename, colspec=None):
    r"""

    Parameters
    ----------
    inputfilename

    Returns
    -------

    """
    with open(inputfilename, "r") as thefile:
        lines = thefile.readlines()
    if colspec is None:
        numvecs = len(lines[0].split())
        collist = range(0, numvecs)
    else:
        collist = colspectolist(colspec)
        if collist[-1] > len(lines[0].split()):
            print("READVECS: too many columns requested - exiting")
            sys.exit()
        if max(collist) > len(lines[0].split()) - 1:
            print("READVECS: requested column", max(collist), "too large - exiting")
            sys.exit()
        numvecs = len(collist)
    inputvec = np.zeros((numvecs, MAXLINES), dtype="float64")
    numvals = 0
    for line in lines:
        if len(line) > 1:
            numvals += 1
            thetokens = line.split()
            outloc = 0
            for vecnum in collist:
                inputvec[outloc, numvals - 1] = np.float64(thetokens[vecnum])
                outloc += 1
    return 1.0 * inputvec[:, 0:numvals]


def readvec(inputfilename):
    r"""Read an array of floats in from a text file.

    Parameters
    ----------
    inputfilename : str
        The name of the text file

    Returns
    -------
    inputdata : 1D numpy float array
        The data from the file

    """
    inputvec = np.zeros(MAXLINES, dtype="float64")
    numvals = 0
    with open(inputfilename, "r") as thefile:
        lines = thefile.readlines()
        for line in lines:
            if len(line) > 1:
                numvals += 1
                inputvec[numvals - 1] = np.float64(line)
    return 1.0 * inputvec[0:numvals]


def readlabels(inputfilename):
    r"""

    Parameters
    ----------
    inputfilename

    Returns
    -------

    """
    inputvec = []
    with open(inputfilename, "r") as thefile:
        lines = thefile.readlines()
        for line in lines:
            inputvec.append(line.rstrip())
    return inputvec


def writedict(thedict, outputfile, lineend=""):
    r"""
    Write all the key value pairs from a dictionary to a text file.

    Parameters
    ----------
    thedict : dict
        A dictionary
    outputfile : str
        The name of the output file
    lineend : { 'mac', 'win', 'linux' }, optional
        Line ending style to use. Default is 'linux'.

    Returns
    -------


    """
    if lineend == "mac":
        thelineending = "\r"
        openmode = "wb"
    elif lineend == "win":
        thelineending = "\r\n"
        openmode = "wb"
    elif lineend == "linux":
        thelineending = "\n"
        openmode = "wb"
    else:
        thelineending = "\n"
        openmode = "w"
    with open(outputfile, openmode) as FILE:
        for key, value in sorted(thedict.items()):
            FILE.writelines(str(key) + ":\t" + str(value) + thelineending)


def writevec(thevec, outputfile, lineend=""):
    r"""Write a vector out to a text file.
    Parameters
    ----------
    thevec : 1D numpy or python array
        The array to write.
    outputfile : str
        The name of the output file
    lineend : { 'mac', 'win', 'linux' }, optional
        Line ending style to use. Default is 'linux'.

    Returns
    -------

    """
    if lineend == "mac":
        thelineending = "\r"
        openmode = "wb"
    elif lineend == "win":
        thelineending = "\r\n"
        openmode = "wb"
    elif lineend == "linux":
        thelineending = "\n"
        openmode = "wb"
    else:
        thelineending = "\n"
        openmode = "w"
    with open(outputfile, openmode) as FILE:
        for i in thevec:
            FILE.writelines(str(i) + thelineending)


# rewritten to guarantee file closure, combines writenpvec and writenpvecs
def writenpvecs(thevecs, outputfile, lineend=""):
    r"""Write out a two dimensional numpy array to a text file

    Parameters
    ----------
    thevecs: 1D or 2D numpy array
        The data to write to the file
    outputfile : str
        The name of the output file
    lineend : { 'mac', 'win', 'linux' }, optional
        Line ending style to use. Default is 'linux'.

    Returns
    -------

    """
    theshape = np.shape(thevecs)
    if lineend == "mac":
        thelineending = "\r"
        openmode = "wb"
    elif lineend == "win":
        thelineending = "\r\n"
        openmode = "wb"
    elif lineend == "linux":
        thelineending = "\n"
        openmode = "wb"
    else:
        thelineending = "\n"
        openmode = "w"
    with open(outputfile, openmode) as FILE:
        if thevecs.ndim == 2:
            for i in range(0, theshape[1]):
                for j in range(0, theshape[0]):
                    FILE.writelines(str(thevecs[j, i]) + "\t")
                FILE.writelines(thelineending)
        else:
            for i in range(0, theshape[0]):
                FILE.writelines(str(thevecs[i]) + thelineending)
