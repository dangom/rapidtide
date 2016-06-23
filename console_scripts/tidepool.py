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
# $Date: 2016/06/10 20:33:32 $
# $Id: tidepool,v 1.25 2016/06/10 20:33:32 frederic Exp $
#
# -*- coding: utf-8 -*-

"""
A simple GUI for looking at the results of a rapidtide analysis
"""

from __future__ import print_function, division

from pyqtgraph.Qt import QtGui, QtCore

import pyqtgraph as pg
import numpy as np
import tidepoolTemplate as uiTemplate
import tide_funcs as tide
import sys
import getopt
import argparse
from OrthoImageItem import OrthoImageItem
import os

from nibabel.affines import apply_affine

aspects = ['None', 'L_A', 'L_C', 'L_I', 'L_IC', 'L_L', 'L_M1', 'L_M2', 'L_M3', 'L_M4', 'L_M5', 'L_M6', 'L_P', 'R_A',
           'R_C', 'R_I', 'R_IC', 'R_L', 'R_M1', 'R_M2', 'R_M3', 'R_M4', 'R_M5', 'R_M6', 'R_P']

# some predefined colortables
g2y2r_state = {'ticks': [(0.5, (255, 255, 0, 255)), (1.0, (255, 0, 0, 255)), (0.0, (0, 255, 0, 255))], 'mode': 'rgb'}
gray_state = {'ticks': [(1.0, (255, 255, 255, 255)), (0.0, (0, 0, 0, 255))], 'mode': 'rgb'}
mask_state = {'ticks': [(0.0, (0, 0, 0, 255)), (1, (255, 255, 255, 0))], 'mode': 'rgb'}

thermal_state = {'ticks': [(0.3333, (185, 0, 0, 255)), (0.6666, (255, 220, 0, 255)),
                           (1, (255, 255, 255, 255)), (0, (0, 0, 0, 255))], 'mode': 'rgb'}
flame_state = {'ticks': [(0.2, (7, 0, 220, 255)), (0.5, (236, 0, 134, 255)), (0.8, (246, 246, 0, 255)),
                         (1.0, (255, 255, 255, 255)), (0.0, (0, 0, 0, 255))], 'mode': 'rgb'}
yellowy_state = {'ticks': [(0.0, (0, 0, 0, 255)), (0.2328863796753704, (32, 0, 129, 255)),
                           (0.8362738179251941, (255, 255, 0, 255)), (0.5257586450247, (115, 15, 255, 255)),
                           (1.0, (255, 255, 255, 255))], 'mode': 'rgb'}
bipolar_state = {'ticks': [(0.0, (0, 255, 255, 255)), (1.0, (255, 255, 0, 255)), (0.5, (0, 0, 0, 255)),
                           (0.25, (0, 0, 255, 255)), (0.75, (255, 0, 0, 255))], 'mode': 'rgb'}
spectrum_state = {'ticks': [(1.0, (255, 0, 255, 255)), (0.0, (255, 0, 0, 255))], 'mode': 'hsv'}
cyclic_state = {'ticks': [(0.0, (255, 0, 4, 255)), (1.0, (255, 0, 0, 255))], 'mode': 'hsv'}
greyclip_state = {'ticks': [(0.0, (0, 0, 0, 255)), (0.99, (255, 255, 255, 255)), (1.0, (255, 0, 0, 255))],
                  'mode': 'rgb'}
grey_state = {'ticks': [(0.0, (0, 0, 0, 255)), (1.0, (255, 255, 255, 255))], 'mode': 'rgb'}
viridis_state = {'ticks': [(0.000, (68, 1, 84)), (0.004, (68, 2, 86)), (0.008, (69, 4, 87)), (0.012, (69, 5, 89)),
                           (0.016, (70, 7, 90)), (0.020, (70, 8, 92)), (0.024, (70, 10, 93)), (0.027, (70, 11, 94)),
                           (0.031, (71, 13, 96)),
                           (0.035, (71, 14, 97)), (0.039, (71, 16, 99)), (0.043, (71, 17, 100)), (0.047, (71, 19, 101)),
                           (0.051, (72, 20, 103)),
                           (0.055, (72, 22, 104)), (0.059, (72, 23, 105)), (0.063, (72, 24, 106)),
                           (0.067, (72, 26, 108)), (0.071, (72, 27, 109)),
                           (0.075, (72, 28, 110)), (0.078, (72, 29, 111)), (0.082, (72, 31, 112)),
                           (0.086, (72, 32, 113)), (0.090, (72, 33, 115)),
                           (0.094, (72, 35, 116)), (0.098, (72, 36, 117)), (0.102, (72, 37, 118)),
                           (0.106, (72, 38, 119)), (0.110, (72, 40, 120)),
                           (0.114, (72, 41, 121)), (0.118, (71, 42, 122)), (0.122, (71, 44, 122)),
                           (0.125, (71, 45, 123)), (0.129, (71, 46, 124)),
                           (0.133, (71, 47, 125)), (0.137, (70, 48, 126)), (0.141, (70, 50, 126)),
                           (0.145, (70, 51, 127)), (0.149, (70, 52, 128)),
                           (0.153, (69, 53, 129)), (0.157, (69, 55, 129)), (0.161, (69, 56, 130)),
                           (0.165, (68, 57, 131)), (0.169, (68, 58, 131)),
                           (0.173, (68, 59, 132)), (0.176, (67, 61, 132)), (0.180, (67, 62, 133)),
                           (0.184, (66, 63, 133)), (0.188, (66, 64, 134)),
                           (0.192, (66, 65, 134)), (0.196, (65, 66, 135)), (0.200, (65, 68, 135)),
                           (0.204, (64, 69, 136)), (0.208, (64, 70, 136)),
                           (0.212, (63, 71, 136)), (0.216, (63, 72, 137)), (0.220, (62, 73, 137)),
                           (0.224, (62, 74, 137)), (0.227, (62, 76, 138)),
                           (0.231, (61, 77, 138)), (0.235, (61, 78, 138)), (0.239, (60, 79, 138)),
                           (0.243, (60, 80, 139)), (0.247, (59, 81, 139)),
                           (0.251, (59, 82, 139)), (0.255, (58, 83, 139)), (0.259, (58, 84, 140)),
                           (0.263, (57, 85, 140)), (0.267, (57, 86, 140)),
                           (0.271, (56, 88, 140)), (0.275, (56, 89, 140)), (0.278, (55, 90, 140)),
                           (0.282, (55, 91, 141)), (0.286, (54, 92, 141)),
                           (0.290, (54, 93, 141)), (0.294, (53, 94, 141)), (0.298, (53, 95, 141)),
                           (0.302, (52, 96, 141)), (0.306, (52, 97, 141)),
                           (0.310, (51, 98, 141)), (0.314, (51, 99, 141)), (0.318, (50, 100, 142)),
                           (0.322, (50, 101, 142)), (0.325, (49, 102, 142)),
                           (0.329, (49, 103, 142)), (0.333, (49, 104, 142)), (0.337, (48, 105, 142)),
                           (0.341, (48, 106, 142)), (0.345, (47, 107, 142)), (0.349, (47, 108, 142)),
                           (0.353, (46, 109, 142)), (0.357, (46, 110, 142)),
                           (0.361, (46, 111, 142)), (0.365, (45, 112, 142)), (0.369, (45, 113, 142)),
                           (0.373, (44, 113, 142)), (0.376, (44, 114, 142)),
                           (0.380, (44, 115, 142)), (0.384, (43, 116, 142)), (0.388, (43, 117, 142)),
                           (0.392, (42, 118, 142)), (0.396, (42, 119, 142)),
                           (0.400, (42, 120, 142)), (0.404, (41, 121, 142)), (0.408, (41, 122, 142)),
                           (0.412, (41, 123, 142)), (0.416, (40, 124, 142)),
                           (0.420, (40, 125, 142)), (0.424, (39, 126, 142)), (0.427, (39, 127, 142)),
                           (0.431, (39, 128, 142)), (0.435, (38, 129, 142)),
                           (0.439, (38, 130, 142)), (0.443, (38, 130, 142)), (0.447, (37, 131, 142)),
                           (0.451, (37, 132, 142)), (0.455, (37, 133, 142)),
                           (0.459, (36, 134, 142)), (0.463, (36, 135, 142)), (0.467, (35, 136, 142)),
                           (0.471, (35, 137, 142)), (0.475, (35, 138, 141)),
                           (0.478, (34, 139, 141)), (0.482, (34, 140, 141)), (0.486, (34, 141, 141)),
                           (0.490, (33, 142, 141)), (0.494, (33, 143, 141)),
                           (0.498, (33, 144, 141)), (0.502, (33, 145, 140)), (0.506, (32, 146, 140)),
                           (0.510, (32, 146, 140)), (0.514, (32, 147, 140)),
                           (0.518, (31, 148, 140)), (0.522, (31, 149, 139)), (0.525, (31, 150, 139)),
                           (0.529, (31, 151, 139)), (0.533, (31, 152, 139)),
                           (0.537, (31, 153, 138)), (0.541, (31, 154, 138)), (0.545, (30, 155, 138)),
                           (0.549, (30, 156, 137)), (0.553, (30, 157, 137)),
                           (0.557, (31, 158, 137)), (0.561, (31, 159, 136)), (0.565, (31, 160, 136)),
                           (0.569, (31, 161, 136)), (0.573, (31, 161, 135)),
                           (0.576, (31, 162, 135)), (0.580, (32, 163, 134)), (0.584, (32, 164, 134)),
                           (0.588, (33, 165, 133)), (0.592, (33, 166, 133)),
                           (0.596, (34, 167, 133)), (0.600, (34, 168, 132)), (0.604, (35, 169, 131)),
                           (0.608, (36, 170, 131)), (0.612, (37, 171, 130)),
                           (0.616, (37, 172, 130)), (0.620, (38, 173, 129)), (0.624, (39, 173, 129)),
                           (0.627, (40, 174, 128)), (0.631, (41, 175, 127)),
                           (0.635, (42, 176, 127)), (0.639, (44, 177, 126)), (0.643, (45, 178, 125)),
                           (0.647, (46, 179, 124)), (0.651, (47, 180, 124)),
                           (0.655, (49, 181, 123)), (0.659, (50, 182, 122)), (0.663, (52, 182, 121)),
                           (0.667, (53, 183, 121)), (0.671, (55, 184, 120)),
                           (0.675, (56, 185, 119)), (0.678, (58, 186, 118)), (0.682, (59, 187, 117)),
                           (0.686, (61, 188, 116)), (0.690, (63, 188, 115)),
                           (0.694, (64, 189, 114)), (0.698, (66, 190, 113)), (0.702, (68, 191, 112)),
                           (0.706, (70, 192, 111)), (0.710, (72, 193, 110)),
                           (0.714, (74, 193, 109)), (0.718, (76, 194, 108)), (0.722, (78, 195, 107)),
                           (0.725, (80, 196, 106)), (0.729, (82, 197, 105)),
                           (0.733, (84, 197, 104)), (0.737, (86, 198, 103)), (0.741, (88, 199, 101)),
                           (0.745, (90, 200, 100)), (0.749, (92, 200, 99)),
                           (0.753, (94, 201, 98)), (0.757, (96, 202, 96)), (0.761, (99, 203, 95)),
                           (0.765, (101, 203, 94)), (0.769, (103, 204, 92)),
                           (0.773, (105, 205, 91)), (0.776, (108, 205, 90)), (0.780, (110, 206, 88)),
                           (0.784, (112, 207, 87)), (0.788, (115, 208, 86)),
                           (0.792, (117, 208, 84)), (0.796, (119, 209, 83)), (0.800, (122, 209, 81)),
                           (0.804, (124, 210, 80)), (0.808, (127, 211, 78)),
                           (0.812, (129, 211, 77)), (0.816, (132, 212, 75)), (0.820, (134, 213, 73)),
                           (0.824, (137, 213, 72)), (0.827, (139, 214, 70)),
                           (0.831, (142, 214, 69)), (0.835, (144, 215, 67)), (0.839, (147, 215, 65)),
                           (0.843, (149, 216, 64)), (0.847, (152, 216, 62)),
                           (0.851, (155, 217, 60)), (0.855, (157, 217, 59)), (0.859, (160, 218, 57)),
                           (0.863, (162, 218, 55)), (0.867, (165, 219, 54)),
                           (0.871, (168, 219, 52)), (0.875, (170, 220, 50)), (0.878, (173, 220, 48)),
                           (0.882, (176, 221, 47)), (0.886, (178, 221, 45)),
                           (0.890, (181, 222, 43)), (0.894, (184, 222, 41)), (0.898, (186, 222, 40)),
                           (0.902, (189, 223, 38)), (0.906, (192, 223, 37)),
                           (0.910, (194, 223, 35)), (0.914, (197, 224, 33)), (0.918, (200, 224, 32)),
                           (0.922, (202, 225, 31)), (0.925, (205, 225, 29)),
                           (0.929, (208, 225, 28)), (0.933, (210, 226, 27)), (0.937, (213, 226, 26)),
                           (0.941, (216, 226, 25)), (0.945, (218, 227, 25)),
                           (0.949, (221, 227, 24)), (0.953, (223, 227, 24)), (0.957, (226, 228, 24)),
                           (0.961, (229, 228, 25)), (0.965, (231, 228, 25)),
                           (0.969, (234, 229, 26)), (0.973, (236, 229, 27)), (0.976, (239, 229, 28)),
                           (0.980, (241, 229, 29)), (0.984, (244, 230, 30)),
                           (0.988, (246, 230, 32)), (0.992, (248, 230, 33)), (0.996, (251, 231, 35)),
                           (1.000, (253, 231, 37))], 'mode': 'rgb'}


def selectFile():
    global datafileroot
    mydialog = QtGui.QFileDialog()
    options = mydialog.Options()
    lagfilename = mydialog.getOpenFileName(options=options, filter="Lag time files (*_lagtimes.nii.gz)")
    datafileroot = str(lagfilename[:-15])


class xyztlocation(QtGui.QWidget):
    "Manage a location in time and space"
    updatedXYZ = QtCore.pyqtSignal()
    updatedT = QtCore.pyqtSignal()
    movieTimer = QtCore.QTimer()


    def __init__(self, xpos, ypos, zpos, tpos, xdim, ydim, zdim, tdim, toffset, tr, affine, \
            XPosSpinBox=None, YPosSpinBox=None, ZPosSpinBox=None, TPosSpinBox=None, \
            XCoordSpinBox=None, YCoordSpinBox=None, ZCoordSpinBox=None, TCoordSpinBox=None, \
            TimeSlider=None, runMovieButton=None):
        QtGui.QWidget.__init__(self)

        self.XPosSpinBox = XPosSpinBox
        self.YPosSpinBox = YPosSpinBox
        self.ZPosSpinBox = ZPosSpinBox
        self.TPosSpinBox = TPosSpinBox
        self.XCoordSpinBox = XCoordSpinBox
        self.YCoordSpinBox = YCoordSpinBox
        self.ZCoordSpinBox = ZCoordSpinBox
        self.TCoordSpinBox = TCoordSpinBox
        self.TimeSlider = TimeSlider
        self.runMovieButton = runMovieButton

        self.xpos = xpos
        self.ypos = ypos
        self.zpos = zpos
        self.setXYZInfo(xdim, ydim, zdim, affine)

        self.tpos = tpos
        self.setTInfo(tdim, tr, toffset)

        self.frametime = 50
        self.movierunning = False
        self.movieTimer.timeout.connect(self.updateMovie)


    def setXYZInfo(self, xdim, ydim, zdim, affine):
        self.xdim = xdim
        self.ydim = ydim 
        self.zdim = zdim
        self.affine = affine
        self.invaffine = np.linalg.inv(self.affine)
        self.xcoord, self.ycoord, self.zcoord = self.vox2real(self.xpos, self.ypos, self.zpos)
        self.setupSpinBox(self.XPosSpinBox, self.getXpos, 0, self.xdim - 1, 1, self.xpos)
        self.setupSpinBox(self.YPosSpinBox, self.getYpos, 0, self.ydim - 1, 1, self.ypos)
        self.setupSpinBox(self.ZPosSpinBox, self.getZpos, 0, self.zdim - 1, 1, self.zpos)
        xllcoord, yllcoord, zllcoord = self.vox2real(0, 0, 0)
        xulcoord, yulcoord, zulcoord = self.vox2real(self.xdim - 1, self.ydim - 1, self.zdim - 1)
        xmin = np.min([xllcoord, xulcoord])
        xmax = np.max([xllcoord, xulcoord])
        ymin = np.min([yllcoord, yulcoord])
        ymax = np.max([yllcoord, yulcoord])
        zmin = np.min([zllcoord, zulcoord])
        zmax = np.max([zllcoord, zulcoord])
        self.setupSpinBox(self.XCoordSpinBox, self.getXcoord, xmin, xmax, (xmax - xmin)/self.xdim, self.xcoord)
        self.setupSpinBox(self.YCoordSpinBox, self.getYcoord, ymin, ymax, (ymax - ymin)/self.ydim, self.ycoord)
        self.setupSpinBox(self.ZCoordSpinBox, self.getZcoord, zmin, zmax, (zmax - zmin)/self.zdim, self.zcoord)


    def setTInfo(self, tdim, tr, toffset):
        self.tdim = tdim
        self.toffset = toffset
        self.tr = tr
        self.tcoord = self.tr2real(self.tpos)
        self.setupSpinBox(self.TPosSpinBox, self.getTpos, 0, self.tdim - 1, 1, self.tpos)
        tllcoord = self.tr2real(0)
        tulcoord = self.tr2real(self.tdim - 1)
        tmin = np.min([tllcoord, tulcoord])
        tmax = np.max([tllcoord, tulcoord])
        self.setupSpinBox(self.TCoordSpinBox, self.getTcoord, tmin, tmax, (tmax - tmin)/self.tdim, self.tcoord)
        self.setupTimeSlider(self.TimeSlider, self.readTimeSlider, 0, self.tdim - 1, self.tpos)
        self.setupRunMovieButton(self.runMovieButton, self.runMovieToggle)

    def setupRunMovieButton(self, thebutton, thehandler):
        if thebutton is not None:
            print('initializing movie button')
            thebutton.setText('Start Movie')
            thebutton.clicked.connect(thehandler)
            
    def setupTimeSlider(self, theslider, thehandler, minval, maxval, currentval):
        if theslider is not None:
            theslider.setRange(minval, maxval)
            theslider.setSingleStep(1)
            theslider.valueChanged.connect(thehandler)

    def setupSpinBox(self, thespinbox, thehandler, minval, maxval, stepsize, currentval):
        if thespinbox is not None:
            thespinbox.setRange(minval, maxval)
            thespinbox.setSingleStep(stepsize)
            thespinbox.setValue(currentval)
            thespinbox.setWrapping(True)
            thespinbox.setKeyboardTracking(False)
            thespinbox.valueChanged.connect(thehandler)

    def updateXYZValues(self):
        #print('resetting XYZ spinbox values')
        if self.XPosSpinBox is not None:
            self.XPosSpinBox.setValue(self.xpos)
        if self.YPosSpinBox is not None:
            self.YPosSpinBox.setValue(self.ypos)
        if self.ZPosSpinBox is not None:
            self.ZPosSpinBox.setValue(self.zpos)
        if self.XCoordSpinBox is not None:
            self.XCoordSpinBox.setValue(self.xcoord)
        if self.YCoordSpinBox is not None:
            self.YCoordSpinBox.setValue(self.ycoord)
        if self.ZCoordSpinBox is not None:
            self.ZCoordSpinBox.setValue(self.zcoord)
        #print('done resetting XYZ spinbox values')
        self.updatedXYZ.emit()
        
    def updateTValues(self):
        #print('resetting T spinbox values')
        if self.TPosSpinBox is not None:
            self.TPosSpinBox.setValue(self.tpos)
        if self.TCoordSpinBox is not None:
            self.TCoordSpinBox.setValue(self.tcoord)
        #print('done resetting T spinbox values')
        self.updatedT.emit()
        
    def real2tr(self, time):
        return(np.round((time - self.toffset)/self.tr, 0))

    def tr2real(self, tpos):
        return(self.toffset + self.tr * tpos)

    def real2vox(self, xcoord, ycoord, zcoord):
        x, y, z = apply_affine(self.invaffine, [xcoord, ycoord, zcoord])
        return(int(np.round(x,0)), int(np.round(y,0)), int(np.round(z,0)))

    def vox2real(self, xpos, ypos, zpos):
        return(apply_affine(self.affine, [xpos, ypos, zpos]))

    def setXYZpos(self, xpos, ypos, zpos):
        self.xpos = xpos
        self.ypos = ypos
        self.zpos = zpos
        self.xcoord, self.ycoord, self.zcoord = self.vox2real(self.xpos, self.ypos, self.zpos)
        self.updateXYZValues()

    def setXYZcoord(self, xcoord, ycoord, zcoord):
        self.xcoord = xcoord
        self.ycoord = ycoord
        self.zcoord = zcoord
        self.xpos, self.ypos, self.zpos = self.real2vox(self.xcoord, self.ycoord, self.zcoord)
        self.updateXYZValues()

    def setTpos(self, tpos):
        if self.tpos != tpos:
            self.tpos = tpos
            self.tcoord = self.tr2real(self.tpos)
            self.updateTValues()

    def setTcoord(self, tcoord):
        if self.tcoord != tcoord:
            self.tcoord = tcoord
            self.tpos = self.real2tr(self.tcoord)
            self.updateTValues()

    def getXpos(self, event):
        #print('entering getXpos')
        newx = int(self.XPosSpinBox.value())
        if self.xpos != newx:
            self.xpos = newx
            self.xcoord, self.ycoord, self.zcoord = self.vox2real(self.xpos, self.ypos, self.zpos)
            self.updateXYZValues()

    def getYpos(self, event):
        #print('entering getYpos')
        newy = int(self.YPosSpinBox.value())
        if self.ypos != newy:
            self.ypos = newy
            self.xcoord, self.ycoord, self.zcoord = self.vox2real(self.xpos, self.ypos, self.zpos)
            self.updateXYZValues()

    def getZpos(self, event):
        #print('entering getZpos')
        newz = int(self.ZPosSpinBox.value())
        if self.zpos != newz:
            self.zpos = newz
            self.xcoord, self.ycoord, self.zcoord = self.vox2real(self.xpos, self.ypos, self.zpos)
            self.updateXYZValues()

    def getTpos(self, event):
        #print('entering getTpos')
        newt = int(self.TPosSpinBox.value())
        if self.tpos != newt:
            self.tpos = newt
            self.tcoord = self.tr2real(self.tpos)
            if self.movierunning:
                self.movieTimer.stop()
                self.movieTimer.start(int(self.tpos))
            self.updateTValues()

    def getXcoord(self, event):
        newxcoord = self.XCoordSpinBox.value()
        if self.xcoord != newxcoord:
            self.xcoord = newxcoord
            self.xpos, self.ypos, self.zpos = self.real2vox(self.xcoord, self.ycoord, self.zcoord)
            self.updateXYZValues()
    
    def getYcoord(self, event):
        newycoord = self.YCoordSpinBox.value()
        if self.ycoord != newycoord:
            self.ycoord = newycoord
            self.xpos, self.ypos, self.zpos = self.real2vox(self.xcoord, self.ycoord, self.zcoord)
            self.updateXYZValues()
    
    def getZcoord(self, event):
        newzcoord = self.ZCoordSpinBox.value()
        if self.zcoord != newzcoord:
            self.zcoord = newzcoord
            self.xpos, self.ypos, self.zpos = self.real2vox(self.xcoord, self.ycoord, self.zcoord)
            self.updateXYZValues()
    
    def getTcoord(self, event):
        newtcoord = self.TCoordSpinBox.value()
        if self.tcoord != newtcoord:
            self.tcoord = newtcoord
            self.tpos = self.real2tr(self.tcoord)
            self.updateTValues()
    
    def readTimeSlider(self):
        self.tpos = self.TimeSlider.value()
        self.updateTValues()

    def updateMovie(self):
        print('entering updateMovie')
        self.tpos = (self.tpos + 1) % self.tdim
        self.updateTValues()

    def runMovieToggle(self, event):
        print('entering runMovieToggle')
        if self.movierunning:
            print('movie is running - turning off')
            self.movierunning = False
            self.movieTimer.stop()
            if self.runMovieButton is not None:
                self.runMovieButton.setText('Start Movie')
        else:
            print('movie is not running - turning on')
            self.movierunning = True
            if self.runMovieButton is not None:
                self.runMovieButton.setText('Stop Movie')
            self.movieTimer.start(int(self.frametime))

    def setFrametime(self, frametime):
        if self.movierunning:
            self.movieTimer.stop()
        self.frametime = frametime
        if self.movierunning:
            self.movieTimer.start(int(self.frametime))
        
class overlay:
    "Store a data overlay and some information about it"

    def __init__(self, name, filename, namebase, funcmask=None, geommask=None, label=None, report=False,
                 lut_state=gray_state):
        print('reading map ',name,' from ',filename,'...')
        self.name = name
        if label is None:
            self.label = name
        else:
            self.label = label
        self.report = report
        self.filename = filename
        self.namebase = namebase
        self.nim, self.data, self.header, self.dims, self.sizes = tide.readfromnifti(self.filename)
        self.xdim, self.ydim, self.zdim, self.tdim = \
            tide.parseniftisizes(self.dims)
        self.xsize, self.ysize, self.zsize, self.tr = \
            tide.parseniftidims(self.sizes)
        self.toffset = self.header['toffset']
        self.mask = None
        self.maskeddata = None
        if geommask is None:
            print('tdim is ',self.tdim)
            print('data shape is ',np.shape(self.data))
            if self.tdim == 1:
                self.geommask = 1.0 + 0.0 * self.data
            else:
                self.geommask = 1.0 + 0.0 * self.data[:, :, :, 0]
        else:
            self.geommask = geommask
        if funcmask is None:
            if self.tdim == 1:
                self.funcmask = 1.0 + 0.0 * self.data
            else:
                self.funcmask = 1.0 + 0.0 * self.data[:, :, :, 0]
        else:
            self.funcmask = funcmask
        self.setGeomMask(self.geommask)
        self.setFuncMask(self.funcmask)
        self.minval = 0
        self.maxval = 0
        self.robustmin = 0
        self.robustmax = 0
        self.dispmin = 0
        self.dispmax = 0
        self.histx = []
        self.histy = []
        self.updateStats()
        self.gradient = pg.GradientWidget(orientation='right', allowAdd=True)
        self.lut_state = lut_state
        self.theLUT = None
        self.setLUT(self.lut_state)
        self.isMNI = False
        if (self.header['sform_code'] == 4) or (self.header['qform_code'] == 4):
            self.isMNI = True
        if self.header['sform_code'] != 0:
            self.affine = self.header.get_sform()
        elif self.header['qform_code'] != 0:
            self.affine = self.header.get_qform()
        else:
            self.affine = self.header.get_base_affine()
        self.invaffine = np.linalg.inv(self.affine)
        self.xpos = 0
        self.ypos= 0
        self.zpos = 0
        self.tpos = 0
        self.xcoord = 0.0
        self.ycoord = 0.0
        self.zcoord = 0.0
        self.tcoord = 0.0

        print('overlay initialized:', self.name, self.filename, self.minval, self.dispmin, self.dispmax, self.maxval)
        #self.summarize()

    def updateStats(self):
        self.minval = self.maskeddata.min()
        self.maxval = self.maskeddata.max()
        self.robustmin, self.robustmax = tide.getfracvals(self.maskeddata, [0.02, 0.98], nozero=True)
        self.dispmin = self.robustmin
        self.dispmax = self.robustmax
        self.histy, self.histx = np.histogram(self.maskeddata[np.where(self.maskeddata != 0.0)],
                                              bins=np.linspace(self.minval, self.maxval, 200))
        # print(self.name,':',self.minval, self.maxval, self.robustmin, self.robustmax)


    def setLabel(self, label):
        self.label = label


    def real2tr(self, time):
        return(np.round((time - self.toffset)/self.tr, 0))

    def tr2real(self, tpos):
        return(self.toffset + self.tr * tpos)


    def real2vox(self, xcoord, ycoord, zcoord, time):
        x, y, z = apply_affine(self.invaffine, [xcoord, ycoord, zcoord])
        t = self.real2tr(time)
        #return(np.concatenate((apply_affine(self.invaffine, [xcoord, ycoord, zcoord]), [self.real2tr(time)]),axis=0))
        return(int(np.round(x,0)), int(np.round(y,0)), int(np.round(z,0)), int(np.round(t,0)))


    def vox2real(self, xpos, ypos, zpos, tpos):
        return(np.concatenate((apply_affine(self.affine, [xpos, ypos, zpos]), [self.tr2real(tpos)]),axis=0))


    def setXYZpos(self, xpos, ypos, zpos):
        self.xpos = xpos
        self.ypos = ypos
        self.zpos = zpos

    def setTpos(self, tpos):
        if tpos > self.tdim - 1:
            self.tpos = self.tdim - 1
        else:
            self.tpos = tpos

    def getFocusVal(self):
        if self.tdim > 1:
            return self.maskeddata[self.xpos, self.ypos, self.zpos, self.tpos]
        else:
            return self.maskeddata[self.xpos, self.ypos, self.zpos]

    def setFuncMask(self, funcmask):
        self.funcmask = funcmask
        if self.funcmask is None:
            if self.tdim == 1:
                self.funcmask = 1.0 + 0.0 * self.data
            else:
                self.funcmask = 1.0 + 0.0 * self.data[:, :, :, 0]
        self.maskData()

    def setGeomMask(self, geommask):
        self.geommask = geommask
        if self.geommask is None:
            if self.tdim == 1:
                self.geommask = 1.0 + 0.0 * self.data
            else:
                self.geommask = 1.0 + 0.0 * self.data[:, :, :, 0]
        self.maskData()

    def maskData(self):
        self.mask = self.geommask * self.funcmask
        self.maskeddata = self.data.copy()
        self.maskeddata[np.where(self.mask < 0.5)] = 0.0
        self.updateStats()

    def setReport(self, report):
        self.report = report

    def setTR(self, trval):
        self.tr = trval

    def settoffset(self, toffset):
        self.toffset = toffset

    def setLUT(self, lut_state):
        self.lut_state = lut_state
        self.gradient.restoreState(lut_state)
        self.theLUT = self.gradient.getLookupTable(512, alpha=True)

    def summarize(self):
        print()
        print('overlay name:         ', self.name)
        print('    label:            ', self.label)
        print('    filename:         ', self.filename)
        print('    namebase:         ', self.namebase)
        print('    xdim:             ', self.xdim)
        print('    ydim:             ', self.ydim)
        print('    zdim:             ', self.zdim)
        print('    tdim:             ', self.tdim)
        print('    isMNI:            ', self.isMNI)
        print('    toffset:          ', self.toffset)
        print('    tr:               ', self.tr)
        print('    min:              ', self.minval)
        print('    max:              ', self.maxval)
        print('    robustmin:        ', self.robustmin)
        print('    robustmax:        ', self.robustmax)
        print('    dispmin:          ', self.dispmin)
        print('    dispmax:          ', self.dispmax)
        print('    data shape:       ', np.shape(self.data))
        print('    masked data shape:', np.shape(self.maskeddata))
        if self.geommask is None:
            print('    geometric mask not set')
        else:
            print('    geometric mask is set')
        if self.funcmask is None:
            print('    functional mask not set')
        else:
            print('    functional mask is set')


def usage():
    print("usage: tidepool [-d DATASET] [-t TR] [-o TOFFSET] [-n] [-a ANAT] [-m MASK]")
    print("")
    print("options:")
    print("    -d DATASET    - specify the root of the rapidtide data (skip opening dialog box)")
    print("    -t TR         - force TR of the correlation plot to TR")
    print("    -o TOFFSET    - force offset of first correlation point to TOFFSET")
    print("    -n            - enable movie mode")
    print("    -r            - enable risetime mode")
    print("    -a ANAT       - use ANAT (a nifti file) as the background anatomic image")
    print("    -m MASK       - use MASK as the geometric mask")
    print("")


def logstatus(thetextbox, thetext):
    thetextbox.moveCursor(QtGui.QTextCursor.End)
    thetextbox.insertPlainText(thetext + '\n')
    sb = thetextbox.verticalScrollBar()
    sb.setValue(sb.maximum())


def getMinDispLimit():
    global ui, overlays, focusmap
    overlays[focusmap].dispmin = ui.dispmin_doubleSpinBox.value()
    updateDispLimits()

def getMaxDispLimit():
    global ui, overlays, focusmap
    overlays[focusmap].dispmax = ui.dispmax_doubleSpinBox.value()
    updateDispLimits()

def updateDispLimits():
    global ui, overlays, focusmap
    ui.dispmin_doubleSpinBox.setRange(overlays[focusmap].minval, overlays[focusmap].maxval)
    ui.dispmax_doubleSpinBox.setRange(overlays[focusmap].minval, overlays[focusmap].maxval)
    ui.dispmin_doubleSpinBox.setSingleStep((overlays[focusmap].maxval - overlays[focusmap].minval) / 100.0)
    ui.dispmax_doubleSpinBox.setSingleStep((overlays[focusmap].maxval - overlays[focusmap].minval) / 100.0)
    ui.dispmin_doubleSpinBox.setValue(overlays[focusmap].dispmin)
    ui.dispmax_doubleSpinBox.setValue(overlays[focusmap].dispmax)
    updateOrthoImages()


def resetDispLimits():
    global overlays, focusmap
    overlays[focusmap].dispmin = overlays[focusmap].minval
    overlays[focusmap].dispmax = overlays[focusmap].maxval
    updateDispLimits()


def resetDispSmart():
    global overlays, focusmap
    overlays[focusmap].dispmin = overlays[focusmap].robustmin
    overlays[focusmap].dispmax = overlays[focusmap].robustmax
    updateDispLimits()


def updateHistogram():
    global hist_ax, overlays, focusmap
    hist_ax.plot(overlays[focusmap].histx, overlays[focusmap].histy,
                 title='Histogram', stepMode=True, fillLevel=0, brush=(0, 0, 255, 80), clear=True)
    updateDispLimits()


def reportAspects():
    print('report aspects')



def toggleAveraging(state):
    global aspectsaverage
    if state == QtCore.Qt.Checked:
        aspectsaverage = True
        print('aspects averaging is turned on')
    else:
        aspectsaverage = False
        print('aspects averaging is turned off')
    


def gray_radioButton_clicked(enabled):
    global imageadj, overlays, focusmap
    if enabled:
        overlays[focusmap].setLUT(gray_state)
        overlays[focusmap].gradient.restoreState(overlays[focusmap].lut_state)
        imageadj.restoreState(overlays[focusmap].lut_state)
        updateLUT()


def thermal_radioButton_clicked(enabled):
    global imageadj, overlays, focusmap
    if enabled:
        overlays[focusmap].setLUT(thermal_state)
        overlays[focusmap].gradient.restoreState(overlays[focusmap].lut_state)
        imageadj.restoreState(overlays[focusmap].lut_state)
        updateLUT()


def GYR_radioButton_clicked(enabled):
    global imageadj, overlays, focusmap
    if enabled:
        overlays[focusmap].setLUT(g2y2r_state)
        overlays[focusmap].gradient.restoreState(overlays[focusmap].lut_state)
        imageadj.restoreState(overlays[focusmap].lut_state)
        updateLUT()


def viridis_radioButton_clicked(enabled):
    global imageadj, overlays, focusmap
    if enabled:
        overlays[focusmap].setLUT(viridis_state)
        overlays[focusmap].gradient.restoreState(overlays[focusmap].lut_state)
        imageadj.restoreState(overlays[focusmap].lut_state)
        updateLUT()


def jet_radioButton_clicked(enabled):
    global imageadj, overlays, focusmap
    if enabled:
        overlays[focusmap].setLUT(cyclic_state)
        overlays[focusmap].gradient.restoreState(overlays[focusmap].lut_state)
        imageadj.restoreState(overlays[focusmap].lut_state)
        updateLUT()


def rainbow_radioButton_clicked(enabled):
    global imageadj, overlays, focusmap
    if enabled:
        overlays[focusmap].setLUT(spectrum_state)
        overlays[focusmap].gradient.restoreState(overlays[focusmap].lut_state)
        imageadj.restoreState(overlays[focusmap].lut_state)
        updateLUT()


def set_lagmask():
    global overlays, loadedfuncmaps, ui
    print('Using valid fit points as functional mask')
    ui.setMask_Button.setText('Valid mask')
    for themap in loadedfuncmaps:
        overlays[themap].setFuncMask('lagmask')
    updateOrthoImages()
    updateHistogram()


def set_refinemask():
    global overlays, loadedfuncmaps, ui
    print('Voxel refinement mask')
    ui.setMask_Button.setText('Refine mask')
    for themap in loadedfuncmaps:
        overlays[themap].setFuncMask('refinemask')
    updateOrthoImages()
    updateHistogram()


def set_nomask():
    global overlays, loadedfuncmaps, ui
    print('disabling functional mask')
    ui.setMask_Button.setText('No Mask')
    for themap in loadedfuncmaps:
        overlays[themap].setFuncMask(None)
    updateOrthoImages()
    updateHistogram()


def set_0p05():
    global overlays, loadedfuncmaps, ui
    print('setting functional mask to p<0.05')
    ui.setMask_Button.setText('p<0.05')
    for themap in loadedfuncmaps:
        overlays[themap].setFuncMask(overlays['p_lt_0p05_mask'].data)
    updateOrthoImages()
    updateHistogram()


def set_0p01():
    global overlays, loadedfuncmaps, ui
    print('setting functional mask to p<0.01')
    ui.setMask_Button.setText('p<0.01')
    for themap in loadedfuncmaps:
        overlays[themap].setFuncMask(overlays['p_lt_0p01_mask'].data)
    updateOrthoImages()
    updateHistogram()


def set_0p005():
    global overlays, loadedfuncmaps, ui
    print('setting functional mask to p<0.005')
    ui.setMask_Button.setText('p<0.005')
    for themap in loadedfuncmaps:
        overlays[themap].setFuncMask(overlays['p_lt_0p005_mask'].data)
    updateOrthoImages()
    updateHistogram()


def set_0p001():
    global overlays, loadedfuncmaps, ui
    print('setting functional mask to p<0.001')
    ui.setMask_Button.setText('p<0.001')
    for themap in loadedfuncmaps:
        overlays[themap].setFuncMask(overlays['p_lt_0p001_mask'].data)
    updateOrthoImages()
    updateHistogram()


def overlay_radioButton_01_clicked(enabled):
    overlay_radioButton_clicked(0, enabled)


def overlay_radioButton_02_clicked(enabled):
    overlay_radioButton_clicked(1, enabled)


def overlay_radioButton_03_clicked(enabled):
    overlay_radioButton_clicked(2, enabled)


def overlay_radioButton_04_clicked(enabled):
    overlay_radioButton_clicked(3, enabled)


def overlay_radioButton_05_clicked(enabled):
    overlay_radioButton_clicked(4, enabled)


def overlay_radioButton_06_clicked(enabled):
    overlay_radioButton_clicked(5, enabled)


def overlay_radioButton_07_clicked(enabled):
    overlay_radioButton_clicked(6, enabled)


def overlay_radioButton_08_clicked(enabled):
    overlay_radioButton_clicked(7, enabled)


def overlay_radioButton_clicked(which, enabled):
    global imageadj, overlays, focusmap, panetomap, ui, overlaybuttons
    global currentloc
    if enabled:
        overlaybuttons[which].setChecked(True)
        #print('selected ', which)
        if panetomap[which] != '':
            focusmap = panetomap[which]
            #print('focusmap set to ', focusmap)
            if overlays[focusmap].lut_state == gray_state:
                #print('checking gray')
                ui.gray_radioButton.setChecked(True)
            elif overlays[focusmap].lut_state == thermal_state:
                #print('checking thermal')
                ui.thermal_radioButton.setChecked(True)
            elif overlays[focusmap].lut_state == g2y2r_state:
                #print('checking GYR')
                ui.GYR_radioButton.setChecked(True)
            elif overlays[focusmap].lut_state == viridis_state:
                #print('checking viridis')
                ui.viridis_radioButton.setChecked(True)
            elif overlays[focusmap].lut_state == cyclic_state:
                #print('checking jet')
                ui.jet_radioButton.setChecked(True)
            else:
                #print('checking rainbow')
                ui.rainbow_radioButton.setChecked(True)

            print('setting t position limits to ',0, overlays[focusmap].tdim - 1)
            currentloc.setTInfo(overlays[focusmap].tdim, overlays[focusmap].tr, overlays[focusmap].toffset)

            updateHistogram()
            updateLUT()


def updateTimepoint(event):
    global data, overlays, timecourse_ax, tr, tpos, timeaxis
    global focusmap
    global vLine
    pos = event.pos()  ## using signal proxy turns original arguments into a tuple
    if overlays[focusmap].tdim > 1:
        mousePoint = timecourse_ax.vb.mapToView(pos)
        tval = mousePoint.x()
        #print('tval=', tval)
        if timeaxis[0] <= tval <= timeaxis[-1]:
            tpos = int((tval - overlays[focusmap].toffset) / overlays[focusmap].tr)
            #print('setting vLine position to ', tval, '(', tpos, ')')
            vLine.setValue(mousePoint.x())
            updateOrthoImages()


def updateLUT():
    global img_colorbar
    global overlays, focusmap
    global harvestcolormaps
    theLUT = overlays[focusmap].theLUT
    img_colorbar.setLookupTable(theLUT)
    if harvestcolormaps:
        print(imageadj.saveState())
    updateOrthoImages()


def updateTimecoursePlot():
    global roisize
    global timeaxis
    global focusmap
    global xpos, ypos, zpos
    global overlays, timecourse_ax
    if overlays[focusmap].tdim > 1:
        selected = overlays[focusmap].data[xpos, ypos, zpos, :]
        timecourse_ax.plot(timeaxis, selected, clear=True)


def mapwithLUT(theimage, themask, theLUT, dispmin, dispmax):
    offset = dispmin
    scale = len(theLUT) / (dispmax - dispmin)
    scaleddata = np.rint((theimage - offset) * scale).astype('int32')
    scaleddata[np.where(scaleddata < 0)] = 0
    scaleddata[np.where(scaleddata > (len(theLUT) - 1))] = len(theLUT) - 1
    mappeddata = theLUT[scaleddata]
    mappeddata[:, :, 3][np.where(themask < 1)] = 0
    return (mappeddata)


def updateTFromControls():
    global mainwin, currentloc
    mainwin.setTpos(currentloc.tpos, emitsignal=False)
    updateOrthoImages()

def updateXYZFromControls():
    global mainwin, currentloc
    mainwin.setXYZpos(currentloc.xpos, currentloc.ypos, currentloc.zpos, emitsignal=False)
    updateOrthoImages()


def updateXYZFromMainWin():
    global mainwin, currentloc
    currentloc.setXYZpos(mainwin.xpos, mainwin.ypos, mainwin.zpos)
    updateOrthoImages()

def updateOrthoImages():
    global hist
    global focusmap
    global maps
    global panetomap
    global ui
    global mainwin, orthoimages
    global currentloc
    global updateTimecoursePlot
    global xdim, ydim, zdim
    global overlays
    global imagadj

    for thismap in panetomap:
        if thismap != '':
            orthoimages[thismap].setXYZpos(currentloc.xpos, currentloc.ypos, currentloc.zpos)
            orthoimages[thismap].setTpos(currentloc.tpos)
    mainwin.setMap(overlays[focusmap])
    mainwin.updateAllViews()

    printfocusvals()
    # ui.time_Slider.setValue(tpos)
    # updateTimecoursePlot()


def printfocusvals():
    global ui, overlays, overlays
    global currentloc
    logstatus(ui.logOutput, 'Print focus vals\n\n')
    for key in overlays:
        #print(key, overlays[key].report)
        if key != 'mnibrainmask':
            #print('key=', key)
            if overlays[key].report:
                #print('gettting ', key, ' value at ', currentloc.xpos, currentloc.ypos, currentloc.zpos, currentloc.tpos)
                overlays[key].setXYZpos(currentloc.xpos, currentloc.ypos, currentloc.zpos)
                overlays[key].setTpos(currentloc.tpos)
                focusval = overlays[key].getFocusVal()
                #print('focusval =', focusval)
                if key != 'aspects':
                    outstring = str(overlays[key].label.ljust(28)) + str(':') + str(focusval)
                    logstatus(ui.logOutput, outstring)
                else:
                    outstring = str(overlays[key].label.ljust(28)) + str(':') + str(aspects[int(focusval)])
                    logstatus(ui.logOutput, outstring)


def loadfuncmaps(thefileroot, theoverlays, thefuncmaps):
    loadedfuncmaps = []
    xdim = 0
    for themap in thefuncmaps:
        if os.path.isfile(thefileroot + themap + '.nii.gz'):
            print('file: ', thefileroot + themap + '.nii.gz', ' exists - reading...')
            thepath, thebase = os.path.split(thefileroot)
            theoverlays[themap] = overlay(themap, thefileroot + themap + '.nii.gz', thebase, report=True)
            if xdim == 0:
                xdim = theoverlays[themap].xdim
                ydim = theoverlays[themap].ydim
                zdim = theoverlays[themap].zdim
                tdim = theoverlays[themap].tdim
                xsize = theoverlays[themap].xsize
                ysize = theoverlays[themap].ysize
                zsize = theoverlays[themap].zsize
                tr = theoverlays[themap].tr
            else:
                if xdim != theoverlays[themap].xdim or ydim != theoverlays[themap].ydim or zdim != theoverlays[themap].zdim:
                    print('overlay dimensions do not match!')
                    sys.exit()
                if xsize != theoverlays[themap].xsize or ysize != theoverlays[themap].ysize or zsize != theoverlays[
                    themap].zsize:
                    print('overlay voxel sizes do not match!')
                    sys.exit()
            loadedfuncmaps.append(themap)
        else:
            print('map: ', thefileroot + themap + '.nii.gz', ' does not exist!')
    print('functional maps loaded:',loadedfuncmaps)
    return(loadedfuncmaps)


def loadanatomics(thefileroot, theoverlays, anatname, MNIcoords, xsize, ysize, zsize):
    try:
        fsldir = os.environ['FSLDIR']
    except KeyError:
        fsldir = None
    referencedir = os.path.join(sys.path[0], 'reference')

    if anatname != '':
        print('using user input anatomic name')
        if os.path.isfile(anatname):
            thepath, thebase = os.path.split(anatname)
            theoverlays['anatomic'] = overlay('anatomic', anatname, thebase)
            print('using ', anatname, ' as background')
            #allloadedmaps.append('anatomic')
            return(True)
        else:
            print('specified file does not exist!')
            return(False)
    elif os.path.isfile(thefileroot + 'highres_head.nii.gz'):
        print('using hires_head anatomic name')
        thepath, thebase = os.path.split(thefileroot)
        theoverlays['anatomic'] = overlay('anatomic', thefileroot + 'highres_head.nii.gz', thebase)
        print('using ', thefileroot + 'highres_head.nii.gz', ' as background')
        #allloadedmaps.append('anatomic')
        return(True)
    elif MNIcoords:
        mniname = ''
        if xsize == 2.0 and ysize == 2.0 and zsize == 2.0:
            print('using 2mm MNI anatomic name')
            if fsldir is not None:
                mniname = os.path.join(fsldir, 'data', 'standard', 'MNI152_T1_2mm.nii.gz')
        elif xsize == 3.0 and ysize == 3.0 and zsize == 3.0:
            print('using 3mm MNI anatomic name')
            mniname = os.path.join(referencedir, 'MNI152_T1_3mm.nii.gz')
        if os.path.isfile(mniname):
            theoverlays['anatomic'] = overlay('anatomic', mniname, 'MNI152')
            print('using ', mniname, ' as background')
            #allloadedmaps.append('anatomic')
            return(True)
        else:
            print('xsize, ysize, zsize=',xsize, ysize, zsize)
            print('MNI template brain ', mniname, ' not loaded')
    elif os.path.isfile(thefileroot + 'mean.nii.gz'):
        thepath, thebase = os.path.split(thefileroot)
        theoverlays['anatomic'] = overlay('anatomic', thefileroot + 'mean.nii.gz', thebase)
        print('using ', thefileroot + 'mean.nii.gz', ' as background')
        #allloadedmaps.append('anatomic')
        return(True)
    else:
        print('no anatomic image loaded')
        return(False)


def loadfuncmasks(thefileroot, theoverlays, thefuncmasks):
    loadedfuncmasks = []
    for themap in thefuncmasks:
        if os.path.isfile(thefileroot + themap + '.nii.gz'):
            thepath, thebase = os.path.split(thefileroot)
            theoverlays[themap] = overlay(themap, thefileroot + themap + '.nii.gz', thebase)
            loadedfuncmasks.append(themap)
        else:
            print('mask: ', thefileroot + themap + '.nii.gz', ' does not exist!')
    return(loadedfuncmasks)


def loadgeommask(thefileroot, theoverlays, geommaskname, MNIcoords, xsize, ysize, zsize):
    referencedir = os.path.join(sys.path[0], 'reference')
    if geommaskname != '':
        if os.path.isfile(geommaskname):
            thepath, thebase = os.path.split(geommaskname)
            theoverlays['geommask'] = overlay('geommask', geommaskname, thebase)
            print('using ', geommaskname, ' as geometric mask')
            #allloadedmaps.append('geommask')
            return(True)
    elif MNIcoords:
        try:
            fsldir = os.environ['FSLDIR']
        except KeyError:
            fsldir = None
        print('fsldir set to ',fsldir)
        if xsize == 2.0 and ysize == 2.0 and zsize == 2.0:
            if fsldir is not None:
                geommaskname = os.path.join(fsldir, 'data', 'standard', 'MNI152_T1_2mm_brain_mask.nii.gz')
        elif xsize == 3.0 and ysize == 3.0 and zsize == 3.0:
            geommaskname = os.path.join(referencedir, 'MNI152_T1_3mm_brain_mask_bin.nii.gz')
        if os.path.isfile(geommaskname):
            thepath, thebase = os.path.split(geommaskname)
            theoverlays['geommask'] = overlay('geommask', geommaskname, thebase)
            print('using ', geommaskname, ' as background')
            #allloadedmaps.append('geommask')
            return(True)
        else:
            print('no geometric mask loaded')
            return(False)
    else:
        print('no geometric mask loaded')
        return(False)


def main():
    global vLine
    global movieTimer, frametime
    global ui, win
    global movierunning
    global focusmap, bgmap
    global maps
    global roi
    global overlays, loadedfuncmaps
    global mainwin, orthoimages, overlaybuttons, panetomap
    global img_colorbar
    global lg_imgsize, scalefacx, scalefacy, scalefacz
    global xdim, ydim, zdim, tdim, xpos, ypos, zpos, tpos
    global xsize, ysize, zsize, tr
    global timeaxis
    global buttonisdown
    global imageadj
    global harvestcolormaps
    global datafileroot
    global aspectsaverage

    # initialize default values
    aspectsaverage = False
    forcetr = False
    forceoffset = False
    usecorrout = False
    userise = False
    MNIcoords = False
    buttonisdown = False
    harvestcolormaps = False
    xdim = 0
    ydim = 0
    zdim = 0
    tdim = 0
    xsize = 0
    ysize = 0
    zsize = 0
    tr = 0
    xpos = 0
    ypos = 0
    zpos = 0
    tpos = 0

    anatname = ''
    geommaskname = ''
    datafileroot = ''

    # get the command line parameters
    # if len(sys.argv) < 2:
    #    usage()
    #    sys.exit()

    offsettime = 0.0
    theparser = argparse.ArgumentParser(description='A program to display the results of a time delay analysis')
    theparser.add_argument('-o', help='Set lag offset', dest='offsettime', type=float)
    theparser.add_argument('-r', help='enable risetime display', dest='userise', action='store_true')
    theparser.add_argument('-n', help='enable movie mode', dest='usecorrout', action='store_true')
    theparser.add_argument('-t', help='Set correlation TR', dest='trval', type=float)
    theparser.add_argument('-d', help='Use this dataset (skip initial selection step)', dest='datafileroot')
    theparser.add_argument('-a', help='Set anatomic mask image', dest='anatname')
    theparser.add_argument('-m', help='Set geometric mask image', dest='geomaskname')
    args = theparser.parse_args()
    if args.offsettime is not None:
        forceoffset = True
        offsetime = args.offsettime
        print('forcing offset time to ', offsettime)
    if args.userise is not None:
        print('enabling risetime display')
    if args.usecorrout:
        usecorrout = True
        print('enabling movie mode')
    theparser.print_help()

    # now scan for optional arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "rd:a:m:nht:o:", ["help"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    for o, a in opts:
        linkchar = ' '
        if o == "-o":
            forceoffset = True
            offsettime = float(a)
            print('forcing offset time to ', offsettime)
        elif o == "-r":
            userise = True
            print('enabling risetime')
        elif o == "-n":
            usecorrout = True
            print('enabling corrout')
        elif o == "-t":
            forcetr = True
            trval = float(a)
            print('forcing correlation TR to ', trval)
        elif o == "-h":
            harvestcolormaps = True
        elif o == "-d":
            datafileroot = a
            print('using ', datafileroot, ' as the root file name ')
        elif o == "-a":
            anatname = a
            print('using ', anatname, ' as the anatomic background image')
        elif o == "-m":
            geommaskname = a
            print('using ', geommaskname, ' as the geometric mask')
        else:
            assert False, "unhandled option"
    app = QtGui.QApplication([])
    print("setting up output window")
    win = QtGui.QMainWindow()
    ui = uiTemplate.Ui_MainWindow()
    ui.setupUi(win)
    win.show()
    win.setWindowTitle("TiDePool")

    # get inputfile root name if necessary
    if datafileroot == '':
        selectFile()

    # movie control
    usetime = False

    # wire up the ortho image windows for mouse interaction
    vb_colorbar = pg.ViewBox(enableMouse=False)
    vb_colorbar.setRange(QtCore.QRectF(0, 0, 25, 256), xRange=(0, 25), yRange=(0, 255), padding=0.0,
                         disableAutoRange=True)
    ui.graphicsView_colorbar.setCentralItem(vb_colorbar)
    vb_colorbar.setAspectLocked()
    img_colorbar = pg.ImageItem()
    vb_colorbar.addItem(img_colorbar)

    colorbar = np.zeros((25, 256), dtype=np.float64)
    for i in range(0, 256):
        colorbar[:, i] = i * (1.0 / 255.0)
    #img_colorbar.setImage(colorbar.astype(np.float64), levels=[0.0, 1.0])
    img_colorbar.setImage(colorbar, levels=[0.0, 1.0])

    # set up the timecourse plot window
    if usetime:
        tcwin = ui.timecourse_graphicsView
        global timecourse_ax
        timecourse_ax = tcwin.addPlot()
        timecourse_ax.setZValue(10)
        vLine = pg.InfiniteLine(angle=90, movable=False, pen='g')
        vLine.setZValue(20)
        timecourse_ax.addItem(vLine)
        timecourse_ax.setTitle('Timecourse')
        timecourse_ax.enableAutoRange()

    # wire up the aspects averaging checkbox
    ui.aspects_checkBox.stateChanged.connect(toggleAveraging)
    ui.report_pushButton.clicked.connect(reportAspects)

    # wire up the radio buttons
    ui.gray_radioButton.toggled.connect(gray_radioButton_clicked)
    ui.thermal_radioButton.toggled.connect(thermal_radioButton_clicked)
    ui.GYR_radioButton.toggled.connect(GYR_radioButton_clicked)
    ui.viridis_radioButton.toggled.connect(viridis_radioButton_clicked)
    ui.jet_radioButton.toggled.connect(jet_radioButton_clicked)
    ui.rainbow_radioButton.toggled.connect(rainbow_radioButton_clicked)

    overlaybuttons = [ui.overlay_radioButton_01,
                      ui.overlay_radioButton_02,
                      ui.overlay_radioButton_03,
                      ui.overlay_radioButton_04,
                      ui.overlay_radioButton_05,
                      ui.overlay_radioButton_06,
                      ui.overlay_radioButton_07,
                      ui.overlay_radioButton_08]
    overlaybuttons[0].toggled.connect(overlay_radioButton_01_clicked)
    overlaybuttons[1].toggled.connect(overlay_radioButton_02_clicked)
    overlaybuttons[2].toggled.connect(overlay_radioButton_03_clicked)
    overlaybuttons[3].toggled.connect(overlay_radioButton_04_clicked)
    overlaybuttons[4].toggled.connect(overlay_radioButton_05_clicked)
    overlaybuttons[5].toggled.connect(overlay_radioButton_06_clicked)
    overlaybuttons[6].toggled.connect(overlay_radioButton_07_clicked)
    overlaybuttons[7].toggled.connect(overlay_radioButton_08_clicked)
    for button in overlaybuttons:
        button.setDisabled(True)
        button.hide()

    overlayGraphicsViews = [ui.overlay_graphicsView_01,
                            ui.overlay_graphicsView_02,
                            ui.overlay_graphicsView_03,
                            ui.overlay_graphicsView_04,
                            ui.overlay_graphicsView_05,
                            ui.overlay_graphicsView_06,
                            ui.overlay_graphicsView_07,
                            ui.overlay_graphicsView_08]

    for theview in overlayGraphicsViews:
        theview.hide()

    # define things for the popup mask menu
    popMenu = QtGui.QMenu(win)
    sel_nomask = QtGui.QAction('No mask', win)
    sel_nomask.triggered.connect(set_nomask)
    sel_lagmask = QtGui.QAction('Valid fit', win)
    sel_lagmask.triggered.connect(set_lagmask)
    sel_refinemask = QtGui.QAction('Voxels used in refine', win)
    sel_refinemask.triggered.connect(set_refinemask)
    sel_0p05 = QtGui.QAction('p<0.05', win)
    sel_0p05.triggered.connect(set_0p05)
    sel_0p01 = QtGui.QAction('p<0.01', win)
    sel_0p01.triggered.connect(set_0p01)
    sel_0p005 = QtGui.QAction('p<0.005', win)
    sel_0p005.triggered.connect(set_0p005)
    sel_0p001 = QtGui.QAction('p<0.001', win)
    sel_0p001.triggered.connect(set_0p001)
    popMenu.addAction(sel_nomask)
    numspecial = 0

    def on_context_menu(point):
        # show context menu
        popMenu.exec_(ui.setMask_Button.mapToGlobal(point))

    ui.setMask_Button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    ui.setMask_Button.customContextMenuRequested.connect(on_context_menu)


    # read in all the datasets
    overlays = {}
    print('loading datasets...')

    # first the functional maps
    funcmaps = ['lagtimes', 'lagstrengths', 'lagsigma', 'R2', 'rCBV', 'fitcoff']
    if userise:
        funcmaps = ['lagtimes', 'lagstrengths', 'lagsigma', 'R2', 'risetime_epoch_0', 'starttime_epoch_0', 'maxamp_epoch_0']
    if usecorrout:
        funcmaps += ['corrout']
    loadedfuncmaps = loadfuncmaps(datafileroot, overlays, funcmaps)
    for themap in loadedfuncmaps:
        if forcetr:
            overlays[themap].setTR(trval)
        if forceoffset:
            overlays[themap].settoffset(offsettime)
        if overlays[themap].isMNI:
            MNIcoords = True

    # report results of load
    print('loaded functional maps: ', loadedfuncmaps)

    allloadedmaps = list(loadedfuncmaps)
    dispmaps = list(loadedfuncmaps)

    # extract some useful information about this dataset from the focusmap
    focusmap = 'lagtimes'

    xdim = overlays[focusmap].xdim
    ydim = overlays[focusmap].ydim
    zdim = overlays[focusmap].zdim
    tdim = overlays[focusmap].tdim
    xsize = overlays[focusmap].xsize
    ysize = overlays[focusmap].ysize
    zsize = overlays[focusmap].zsize
    tr = overlays[focusmap].tr

    # then load the anatomics
    if loadanatomics(datafileroot, overlays, anatname, MNIcoords, xsize, ysize, zsize):
        allloadedmaps.append('anatomic')

    # then the functional masks
    funcmasks = ['lagmask', 'p_lt_0p05_mask', 'p_lt_0p01_mask', 'p_lt_0p005_mask', 'p_lt_0p001_mask']
    loadedfuncmasks = loadfuncmasks(datafileroot, overlays, funcmasks)

    # then the geometric masks
    if loadgeommask(datafileroot, overlays, geommaskname, MNIcoords, xsize, ysize, zsize):
        allloadedmaps.append('geommask')

    if MNIcoords and xsize == 2.0 and ysize == 2.0 and zsize == 2.0:
        referencedir = os.path.join(sys.path[0], 'reference')
        aspectsname = os.path.join(referencedir, 'ASPECTS.nii.gz')
        if os.path.isfile(aspectsname):
            overlays['aspects'] = overlay('aspects', aspectsname, 'ASPECTS', report=True)
            allloadedmaps.append('aspects')
            dispmaps.append('aspects')
        else:
            print('ASPECTS template: ', aspectsname, ' does not exist!')
    try:
        test = overlays['aspects']
        ui.aspects_checkBox.show()
        ui.aspects_checkBox.setDisabled(False)
        ui.report_pushButton.show()
        ui.report_pushButton.setDisabled(False)
    except KeyError:
        ui.aspects_checkBox.hide()
        ui.aspects_checkBox.setDisabled(True)
        ui.report_pushButton.hide()
        ui.report_pushButton.setDisabled(True)
    print('done')

    win.setWindowTitle('TiDePool - ' + datafileroot)

    # set the background image
    if 'anatomic' in overlays:
        bgmap = 'anatomic'
    else:
        bgmap = None

    # set up the timecourse plot window
    xpos = xdim / 2
    timeaxis = np.r_[0.0:overlays[focusmap].tdim] * overlays[focusmap].tr + overlays[focusmap].toffset
    ypos = ydim / 2
    zpos = zdim / 2
    tpos = 0

    # set position and scale of images
    lg_imgsize = 256.0
    sm_imgsize = 32.0
    xfov = xdim * xsize
    yfov = ydim * ysize
    zfov = zdim * zsize
    # print('fovs=',xfov,yfov,zfov)
    maxfov = np.max([xfov, yfov, zfov])
    # print('maxfov=',maxfov)
    scalefacx = (lg_imgsize / maxfov) * xsize
    scalefacy = (lg_imgsize / maxfov) * ysize
    scalefacz = (lg_imgsize / maxfov) * zsize

    # configure the gradient scale
    imageadj = pg.GradientWidget(orientation='right', allowAdd=True)
    imageadj.restoreState(gray_state)
    if harvestcolormaps:
        ui.largeimage_horizontalLayout.addWidget(imageadj)

    defaultdict = {
        'lagmask':
            {
                'colormap': gray_state,
                'label': 'Lag mask',
                'funcmask': None},
        'geommask':
            {
                'colormap': gray_state,
                'label': 'Geometric mask',
                'funcmask': None},
        'refinemask':
            {
                'colormap': gray_state,
                'label': 'Refine mask',
                'funcmask': None},
        'p_lt_0p05_mask':
            {
                'colormap': gray_state,
                'label': 'p<0.05',
                'funcmask': None},
        'p_lt_0p01_mask':
            {
                'colormap': gray_state,
                'label': 'p<0.01',
                'funcmask': None},
        'p_lt_0p005_mask':
            {
                'colormap': gray_state,
                'label': 'p<0.005',
                'funcmask': None},
        'p_lt_0p001_mask':
            {
                'colormap': gray_state,
                'label': 'p<0.001',
                'funcmask': None},
        'risetime_epoch_0':
            {
                'colormap': viridis_state,
                'label': 'Rise times',
                'funcmask': 'p_lt_0p05_mask'},
        'maxamp_epoch_0':
            {
                'colormap': viridis_state,
                'label': 'CVR',
                'funcmask': 'p_lt_0p05_mask'},
        'starttime_epoch_0':
            {
                'colormap': viridis_state,
                'label': 'Start times',
                'funcmask': 'p_lt_0p05_mask'},
        'lagtimes':
            {
                'colormap': viridis_state,
                'label': 'Lag times',
                'funcmask': 'p_lt_0p05_mask'},
        'lagstrengths':
            {
                'colormap': thermal_state,
                'label': 'Correlation coefficient',
                'funcmask': 'p_lt_0p05_mask'},
        'lagsigma':
            {
                'colormap': spectrum_state,
                'label': 'MTT',
                'funcmask': 'p_lt_0p05_mask'},
        'rCBV':
            {
                'colormap': thermal_state,
                'label': 'rCBV',
                'funcmask': 'p_lt_0p05_mask'},
        'R2':
            {
                'colormap': thermal_state,
                'label': 'R2',
                'funcmask': 'p_lt_0p05_mask'},
        'corrout':
            {
                'colormap': thermal_state,
                'label': 'Correlation function',
                'funcmask': 'p_lt_0p05_mask'},
        'anatomic':
            {
                'colormap': gray_state,
                'label': 'Anatomic image',
                'funcmask': None},
        'aspects':
            {
                'colormap': spectrum_state,
                'label': 'ASPECTS territories',
                'funcmask': None},
        'fitcoff':
            {
                'colormap': thermal_state,
                'label': 'GLM fit coefficient',
                'funcmask': 'p_lt_0p05_mask'}}

    print('setting overlay defaults')
    for themap in allloadedmaps + loadedfuncmasks:
        overlays[themap].setLUT(defaultdict[themap]['colormap'])
        overlays[themap].setLabel(defaultdict[themap]['label'])
    print('done setting overlay defaults')

    panetomap = ['', '', '', '', '', '', '', '', '']

    print('setting geometric masks')
    if 'geommask' in overlays:
        thegeommask = overlays['geommask'].data
        print('setting geometric mask')
    else:
        thegeommask = None
        print('setting geometric mask to None')

    for theoverlay in loadedfuncmaps:
        overlays[theoverlay].setGeomMask(thegeommask)
    print('done setting geometric masks')

    print('setting functional masks')
    for theoverlay in loadedfuncmaps:
        if 'p_lt_0p05_mask' in overlays:
            overlays[theoverlay].setFuncMask(overlays['p_lt_0p05_mask'].data)
            ui.setMask_Button.setText('p<0.05')
        else:
            overlays[theoverlay].setFuncMask(overlays['lagmask'].data)
            ui.setMask_Button.setText('Valid mask')
    print('done setting functional masks')

    if 'anatomic' in overlays:
        overlays['anatomic'].setFuncMask(None)
        overlays['anatomic'].setGeomMask(None)

    if 'aspects' in overlays:
        aspectmask = overlays['aspects'].data.copy()
        aspectmask[np.where(aspectmask > 0.5)] = 1
        aspectmask[np.where(aspectmask < 1)] = 0
        overlays['aspects'].setGeomMask(aspectmask)
        overlays['aspects'].setFuncMask(None)

    verbose = False
    if verbose:
        for theoverlay in overlays:
            overlays[theoverlay].summarize()

    def loadpane(themap, thepane, view, button, panemap, orthoimages, bgmap=None):
        if bgmap is None:
            orthoimages[themap.name] = OrthoImageItem(themap, view[thepane], button=button[thepane], 
                                                 imgsize=sm_imgsize)
        else:
            orthoimages[themap.name] = OrthoImageItem(themap, view[thepane], button=button[thepane], bgmap=bgmap,
                                                 imgsize=sm_imgsize)
        panemap[thepane] = themap.name

    print('focusmap is:', focusmap, 'bgmap is:', bgmap)
    if bgmap is None:
        mainwin = OrthoImageItem(overlays[focusmap], ui.main_graphicsView, imgsize=lg_imgsize,
                            enableMouse=True)
    else:
        mainwin = OrthoImageItem(overlays[focusmap], ui.main_graphicsView, bgmap=overlays[bgmap], imgsize=lg_imgsize,
                            enableMouse=True)
    mainwin.updated.connect(updateXYZFromMainWin)

    orthoimages = {}
    print('loading panes')
    for idx, themap in enumerate(dispmaps):
        if bgmap is None:
            loadpane(overlays[themap], idx, overlayGraphicsViews, overlaybuttons, panetomap, orthoimages)
        else:
            loadpane(overlays[themap], idx, overlayGraphicsViews, overlaybuttons, panetomap, orthoimages,
                 bgmap=overlays[bgmap])
    print('done loading panes')

    print('about to set up the histogram')
    # set up the histogram window
    global hist_ax
    histwin = ui.histogram_graphicsView
    hist_ax = histwin.addPlot()
    ui.resetDispLimits_Button.clicked.connect(resetDispLimits)
    ui.resetDispSmart_Button.clicked.connect(resetDispSmart)
    ui.saveDisp_Button.clicked.connect(mainwin.saveDisp)
    ui.dispmin_doubleSpinBox.valueChanged.connect(getMinDispLimit)
    ui.dispmax_doubleSpinBox.valueChanged.connect(getMaxDispLimit)

    if len(loadedfuncmasks) > 0:
        popMenu.addSeparator()
        """
        if 'lagmask' in loadedfuncmasks:
            popMenu.addAction(sel_lagmask)
            numspecial += 1
        if 'refinemask' in loadedfuncmasks:
            popMenu.addAction(sel_refinemask)
            numspecial += 1
        if numspecial > 0:
            popMenu.addSeparator()
        """
        if 'p_lt_0p05_mask' in loadedfuncmasks:
            popMenu.addAction(sel_0p05)
        if 'p_lt_0p01_mask' in loadedfuncmasks:
            popMenu.addAction(sel_0p01)
        if 'p_lt_0p005_mask' in loadedfuncmasks:
            popMenu.addAction(sel_0p005)
        if 'p_lt_0p001_mask' in loadedfuncmasks:
            popMenu.addAction(sel_0p001)

    # initialize the location picker
    global currentloc
    currentloc = \
            xyztlocation(xpos, ypos, zpos, tpos, xdim, ydim, zdim, tdim,
            overlays[focusmap].toffset, overlays[focusmap].tr, overlays[focusmap].affine,
            XPosSpinBox=ui.pixnumX_doubleSpinBox,
            YPosSpinBox=ui.pixnumY_doubleSpinBox,
            ZPosSpinBox=ui.pixnumZ_doubleSpinBox,
            TPosSpinBox=ui.pixnumT_doubleSpinBox, 
            XCoordSpinBox=ui.coordX_doubleSpinBox,
            YCoordSpinBox=ui.coordY_doubleSpinBox,
            ZCoordSpinBox=ui.coordZ_doubleSpinBox,
            TCoordSpinBox=ui.coordT_doubleSpinBox,
            TimeSlider=ui.TimeSlider,
            runMovieButton=ui.runMovieButton)
    currentloc.updatedXYZ.connect(updateXYZFromControls)
    currentloc.updatedT.connect(updateTFromControls)
    updateHistogram()

    updateLUT()

    # zoom to fit imageo
    # timecourse_ax.enableAutoRange()

    # select the first pane
    overlay_radioButton_01_clicked(True)

    # have to do this after the windows are created
    imageadj.sigGradientChanged.connect(updateLUT)
    # timecourse_ax.scene().sigMouseClicked.connect(updateTimepoint)

    updateOrthoImages()
    updateTimecoursePlot()

    QtGui.QApplication.instance().exec_()


if __name__ == "__main__":
    main()