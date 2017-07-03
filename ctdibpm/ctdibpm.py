#!/usr/bin/env python

#############################################################################
##
## Copyright (C) 2004-2005 Trolltech AS. All rights reserved.
##
## This file is part of the example classes of the Qt Toolkit.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following information to ensure GNU
## General Public Licensing requirements will be met:
## http://www.trolltech.com/products/qt/opensource.html
##
## If you are unsure which license is appropriate for your use, please
## review the following information:
## http://www.trolltech.com/products/qt/licensing.html or contact the
## sales department at sales@trolltech.com.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
#############################################################################

# Alba imports
import PyTango
from taurus.core.util import argparse
from taurus.external.qt import uic
from taurus.qt.qtgui.container import TaurusMainWindow
from taurus.qt.qtgui.application import TaurusApplication

import rcc_icons
from liberatab import *
from screenshot import Screenshot

# Standard python imports
import sys
import time
import string
import calendar
import os
import webbrowser
from datetime import datetime
from optparse import OptionParser

__version = '1.1.4'  # managed by bumpversion, do not edit manually

# Enumeration Values
SWITCHES_DIRECT         = 0
SWITCHES_AUTO           = 1

SWITCH_DIRECT           = 15
SWITCH_AUTO             = 255

CLOCK_SOURCE_INTERNAL   = 0
CLOCK_SOURCE_EXTERNAL   = 1

DSC_OFF                 = 0
DSC_UNITY               = 1
DSC_AUTO                = 2
DSC_SAVE                = 3

INTERLOCK_MODE_OFF      = 0
INTERLOCK_MODE_ON       = 1
INTERLOCK_MODE_ON_GAIN  = 2

OVERF_DUR_MAX           = 1050
ACTIVE_WIDGET           = 1

# Constants
SERVER_NAME   = "LiberaAcquisator/*"
CLASS_NAME    = "LiberaAcquisator"

#Default save/load paths and files
DEFAULT_PATH = "/tmp/bootservertmp/operator/"
GAIN_FILENAME = DEFAULT_PATH + "gain.conf"

DOC_URL = "http://www.cells.es/Intranet/Divisions/Computing/Controls/Help/DI/BPM/"


class MainWindow(QtGui.QMainWindow):

        def __init__(self, parent=None,liberaDeviceName=None):

                # Get graphical information
                QtGui.QMainWindow.__init__(self, parent=parent)
                uipath = os.path.join(os.path.dirname(__file__),
                                    "ui",
                                    "ui_libera.ui")
                self.ui = uic.loadUi(uipath, self)
                
                # Add statusbar info to toolbar to save space. Insted of adding this to the toolBar,
                # you can add it to the status bar. You'll have to modify the main ui file to include
                # a status bar and then substitute self.ui.toolBar.addWidget(self.LiberaStatusBar) by:
                #self.ui.statusbar.addPermanentWidget(self.LiberaStatusBar)
                self.LiberaStatusBar = LiberaStatusBar(self)
                self.ui.toolBar.addWidget(self.LiberaStatusBar)

                # Initialize devices and devices names
                self.dp = None
                self.dsPyName = None
                self.dsCppName = None

                # 'File' Menu Actions
                QtCore.QObject.connect(self.ui.actionLiberaStart,   QtCore.SIGNAL("triggered()"), self.onActionLiberaStart)
                QtCore.QObject.connect(self.ui.actionLiberaStop ,   QtCore.SIGNAL("triggered()"), self.onActionLiberaStop)
                QtCore.QObject.connect(self.ui.actionLiberaRestart, QtCore.SIGNAL("triggered()"), self.onActionLiberaRestart)
                QtCore.QObject.connect(self.ui.actionLiberaReboot,  QtCore.SIGNAL("triggered()"), self.onActionLiberaReboot)
                QtCore.QObject.connect(self.ui.actionLiberaDSInit,  QtCore.SIGNAL("triggered()"), self.onActionLiberaDSInit)
                QtCore.QObject.connect(self.ui.actionOpen,          QtCore.SIGNAL("triggered()"), self.onActionOpen)
                QtCore.QObject.connect(self.ui.actionSave,          QtCore.SIGNAL("triggered()"), self.onActionSave)
                QtCore.QObject.connect(self.ui.actionPrint,         QtCore.SIGNAL("triggered()"), self.onActionPrint)
                QtCore.QObject.connect(self.ui.actionScreenshot,    QtCore.SIGNAL("triggered()"), self.onActionScreenshot)
                QtCore.QObject.connect(self.ui.actionQuit,          QtCore.SIGNAL("triggered()"), self.onActionQuit)

                # 'Unit' Menu Actions
                QtCore.QObject.connect(self.ui.actionConnectToLibera, QtCore.SIGNAL("triggered()"), self.onActionConnectToLibera)
                QtCore.QObject.connect(self.ui.actionSynchronize, QtCore.SIGNAL("triggered()"), self.onActionSynchronize)

                # 'Mode' Menu Actions
                QtCore.QObject.connect(self.ui.actionADCTab, QtCore.SIGNAL("triggered()"), self.onActionADCTab)
                QtCore.QObject.connect(self.ui.actionDDTab1, QtCore.SIGNAL("triggered()"), self.onActionDDTab1)
                QtCore.QObject.connect(self.ui.actionDDTab2,   QtCore.SIGNAL("triggered()"), self.onActionDDTab2)
                QtCore.QObject.connect(self.ui.actionPMTab1, QtCore.SIGNAL("triggered()"), self.onActionPMTab1)
                QtCore.QObject.connect(self.ui.actionPMTab2,   QtCore.SIGNAL("triggered()"), self.onActionPMTab2)
                QtCore.QObject.connect(self.ui.actionSATab1, QtCore.SIGNAL("triggered()"), self.onActionSATab1)
                QtCore.QObject.connect(self.ui.actionSATab2,   QtCore.SIGNAL("triggered()"), self.onActionSATab2)
                QtCore.QObject.connect(self.ui.actionFATab1, QtCore.SIGNAL("triggered()"), self.onActionFATab1)
                QtCore.QObject.connect(self.ui.actionFATab2,   QtCore.SIGNAL("triggered()"), self.onActionFATab2)
                QtCore.QObject.connect(self.ui.actionGain,    QtCore.SIGNAL("triggered()"), self.onActionGain)
                QtCore.QObject.connect(self.ui.actionLog,    QtCore.SIGNAL("triggered()"), self.onActionLog)

                # 'Help' Menu Actions
                QtCore.QObject.connect(self.ui.actionHelp, QtCore.SIGNAL("triggered()"), self.onActionHelp)
                QtCore.QObject.connect(self.ui.actionAbout, QtCore.SIGNAL("triggered()"), self.onActionAbout)

                #Keep DD single acquisition check boxes synchronized
                QtCore.QObject.connect(self.ui.DDcheckSingle1, QtCore.SIGNAL("toggled(bool)"), self.ui.DDcheckSingle2, QtCore.SLOT("setChecked(bool)") )
                QtCore.QObject.connect(self.ui.DDcheckSingle2, QtCore.SIGNAL("toggled(bool)"), self.ui.DDcheckSingle1, QtCore.SLOT("setChecked(bool)") )

                #Keep DD Decimation acquisition check boxes synchronized
                #QtCore.QObject.connect(self.ui.DDDecimation1, QtCore.SIGNAL("toggled(bool)"), self.ui.DDDecimation2, QtCore.SLOT("setChecked(bool)") )
                #QtCore.QObject.connect(self.ui.DDDecimation2, QtCore.SIGNAL("toggled(bool)"), self.ui.DDDecimation1, QtCore.SLOT("setChecked(bool)") )
                
                # Add Gain Scheme tab
                self.gainScheme = GainScheme(self)
                self.ui.tabWidget.insertTab(self.ui.tabWidget.count(),self.gainScheme,self.tr("Gain Scheme"))

                # Add log tab
                self.log = Log(self)
                self.ui.tabWidget.insertTab(self.ui.tabWidget.count(),self.log,self.tr("Log"))

                # Initialize time window
                self.settime = SetTime(self)
                # Initialize time synchronization window
                self.synctime = SyncTime(self)
                # Initialize screenshot window
                self.screenshot = Screenshot()

                self.setTab()

                # show maximized
                self.showMaximized()

                # hide duplicated control groupboxes (asked by user, but will
                # probably change his mind, so just hide them, don't remove)
                self.ui.groupBoxDD2.hide()
                self.ui.groupBoxPM2.hide()
                self.ui.groupBoxSA2.hide()
                self.ui.groupBoxFA2.hide()

                #configure environment and post mortem configuration dock widgets
                self.setDockNestingEnabled(True)

                self.environment = Environment(self) 
                self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.environment)

                self.postMortemConfiguration = PostMortemConfiguration(self) 
                self.tabifyDockWidget(self.environment, self.postMortemConfiguration)

                #Connect to libera number or libera device (if any specified)
                if liberaDeviceName:
                    self.connectLibera(liberaDeviceName)
                else:
                    pass

        def setTab(self):

                # Set ADC tab
                ADCTabWidgets = {
                "tabname"       : "ADC",
                "plot1"         : [self.ui.ADCplot, "ADCChannelA","ADCChannelB","ADCChannelC","ADCChannelD"],
                "plot2"         : [None, None],
                "start"         : [self.ui.ADCstart, "ADCAcquire"],
                "stop"          : [self.ui.ADCstop, "ADCStop"],
                "save"          : [self.ui.ADCsave, "ADCSave"],
                "resetPM"       : [None, None],
                "samples"       : [self.ui.ADCsamples, "ADCNSamples"],
                "samplesRB"     : [self.ui.ADCsamplesRB, 'ADCNSamples'],
                "loops"         : [self.ui.ADCloops, "ADCNLoops"],
                "loopsRB"       : [self.ui.ADCloopsRB, 'ADCNLoops'],
                "triggercounts" : [self.ui.ADCtriggers, "ADCLoopCounter"],
                "peakA"         : [self.ui.ADCPeakA, "ADCChannelAPeak"],
                "peakB"         : [self.ui.ADCPeakB, "ADCChannelBPeak"],
                "peakC"         : [self.ui.ADCPeakC, "ADCChannelCPeak"],
                "peakD"         : [self.ui.ADCPeakD, "ADCChannelDPeak"],
                "singleLoop"    : [self.ui.ADCcheckSingle, None],
                "timestamp"     : [self.ui.ADCtimestamp, "ADCTimestamp"],
                "timestampRB"   : [self.ui.ADCtimestampRB, "ADCTimestamp"],
                "filename"      : [None, "ADCFileName"],
                "enabled"       : [None, "ADCEnabled"],
                }
                self.ADCTab = LiberaTab(ADCTabWidgets)

                # Set DDrate tab
                DDTab1Widgets = {
                "tabname"       : "DDXZVolt",
                "plot1"         : [self.ui.DDplotA1,"XPosDD","ZPosDD"],
                "plot2"         : [self.ui.DDplotA2,"VaDD","VbDD","VcDD","VdDD"],
                "start"         : [self.ui.DDstart1, 'DDAcquire'],
                "stop"          : [self.ui.DDstop1, "DDStop"],
                "save"          : [self.ui.DDsave, "DDSave"],
                "samples"       : [self.ui.DDNSamples1, 'DDNSamples'],
                "samplesRB"     : [self.ui.DDNSamplesRB1, 'DDNSamples'],
                "loops"         : [self.ui.DDloops1, 'DDNLoops'],
                "loopsRB"       : [self.ui.DDloopsRB1, 'DDNLoops'],
                "triggercounts" : [self.ui.DDTriggers1, 'DDLoopCounter'],
                "resetPM"       : [None, None],
                "decimation"    : [self.ui.DDDecimation1, 'DDDecimationFactor'],
                "decimationRB"  : [self.ui.DDDecimationRB1, 'DDDecimationFactor'],
                "singleLoop"    : [self.ui.DDcheckSingle1, None],
                "timestamp"     : [self.ui.DDtimestamp, "DDTimestamp"],
                "timestampRB"   : [self.ui.DDtimestampRB, "DDTimestamp"],
                "filename"      : [None, "DDFileName"],
                "enabled"       : [None, "DDEnabled"],
                }
                self.DDTab1 = LiberaTab(DDTab1Widgets)

                # Set DDrate tab
                DDTab2Widgets = {
                "tabname"       : "DDQSum",
                "plot1"         : [self.ui.DDplotB1, "QuadDD"],
                "plot2"         : [self.ui.DDplotB2, "SumDD"],
                "start"         : [self.ui.DDstart2, "DDAcquire"],
                "singleLoop"    : [self.ui.DDcheckSingle2, None],
                "stop"          : [self.ui.DDstop2, "DDStop"],
                "save"          : [None, None],
                "resetPM"       : [None, None],
                "samples"       : [self.ui.DDNSamples2, 'DDNSamples'],
                "samplesRB"     : [self.ui.DDNSamplesRB2, 'DDNSamples'],
                "loops"         : [self.ui.DDloops2, 'DDNLoops'],
                "loopsRB"       : [self.ui.DDloopsRB2, 'DDNLoops'],
                "triggercounts" : [self.ui.DDTriggers2, 'DDLoopCounter'],
                "decimation"    : [self.ui.DDDecimation2, 'DDDecimationFactor'],
                "decimationRB"  : [self.ui.DDDecimationRB2, 'DDDecimationFactor'],
                "singleLoop"    : [self.ui.DDcheckSingle1, None],
                "timestamp"     : [self.ui.DDtimestamp, "DDTimestamp"],
                "timestampRB"   : [self.ui.DDtimestampRB, "DDTimestamp"],
                "enabled"       : [None, "DDEnabled"],
                "filename"      : [None, "DDFileName"],
                }
                self.DDTab2 = LiberaTab(DDTab2Widgets)

                # Set PM tab
                PMTab1Widgets = {
                "tabname"       : "PMXZVolt",
                "plot1"         : [self.ui.PMplotA1,"XPosPM","ZPosPM"],
                "plot2"         : [self.ui.PMplotA2,"VaPM","VbPM","VcPM","VdPM"],
                "start"         : [self.ui.PMstart1, "PMAcquire"],
                "stop"          : [None, None],
                "save"          : [self.ui.PMsave, "PMSave"],
                "resetPM"       : [None, None],
                "samples"       : [self.ui.PMNSamples1, "PMNSamples"],
                "samplesRB"     : [self.ui.PMNSamplesRB1, "PMNSamples"],
                "loops"         : [None, None],
                "resetPM"       : [self.ui.PMreset1, "PMResetFlag"],
                "singleLoop"    : [None, None],
                "timestamp"     : [self.ui.PMtimestamp, "PMTimestamp"],
                "timestampRB"   : [self.ui.PMtimestampRB, "PMTimestamp"],
                "filename"      : [None, "PMFileName"],
                }
                self.PMTab1 = LiberaTab(PMTab1Widgets)

                # Set PM tab
                PMTab2Widgets = {
                "tabname"       : "PMQSum",
                "plot1"         : [self.ui.PMplotB1, "QuadPM"],
                "plot2"         : [self.ui.PMplotB2, "SumPM"],
                "start"         : [self.ui.PMstart2, "PMAcquire"],
                "stop"          : [None, None],
                "save"          : [None, None],
                "resetPM"       : [None, None],
                "samples"       : [self.ui.PMNSamples2, "PMNSamples"],
                "samplesRB"     : [self.ui.PMNSamplesRB2, "PMNSamples"],
                "singleLoop"    : [None, None],
                "timestamp"     : [self.ui.PMtimestamp, "PMTimestamp"],
                "timestampRB"   : [self.ui.PMtimestampRB, "PMTimestamp"],
                "filename"      : [None, "PMFileName"],
                }
                self.PMTab2 = LiberaTab(PMTab2Widgets)

                # Set SA tab
                SATab1Widgets = {
                "tabname"       : "SAXZVolt",
                "plot1"         : [self.ui.SAplotA1, "XPosSA","ZPosSA"],
                "plot2"         : [self.ui.SAplotA2, "VaSA","VbSA","VcSA","VdSA"],
                "start"         : [self.ui.SAstart1, "SAAcquire"], 
                "stop"          : [self.ui.SAstop1, "SAStop"],
                "save"          : [None, None],
                "resetPM"       : [None, None],

                "samples"       : [self.ui.SANSamples1, "SANSamples"],
                "samplesRB"     : [self.ui.SANSamplesRB1, "SANSamples"],
                "singleLoop"    : [None, None],
                "timestamp"     : [self.ui.SAtimestamp1, "SATimestamp"],
                "timestampRB"   : [self.ui.SAtimestampRB1, "SATimestamp"],
                "timesleep"     : [self.ui.SAtimesleep1, "SASleep"],
                "timesleepRB"   : [self.ui.SAtimesleepRB1, "SASleep"],
                "filename"      : [None, "SAFileName"],
                "enabled"       : [None, "SAEnabled"],
                }
                self.SATab1 = LiberaTab(SATab1Widgets)

                # Set SA tab
                SATab2Widgets = {
                "tabname"       : "SAQSum",
                "plot1"         : [self.ui.SAplotB1, "QuadSA"],
                "plot2"         : [self.ui.SAplotB2, "SumSA"],
                "start"         : [self.ui.SAstart2, "SAAcquire"], 
                "stop"          : [self.ui.SAstop2, "SAStop"],
                "save"          : [None, None],
                "resetPM"       : [None, None],
                "singleLoop"    : [None, None],
                "timestamp"     : [None, None],
                "samples"       : [self.ui.SANSamples2, "SANSamples"],
                "samplesRB"     : [self.ui.SANSamplesRB2, "SANSamples"],
                "timestamp"     : [self.ui.SAtimestamp2, "SATimestamp"],
                "timestampRB"   : [self.ui.SAtimestampRB2, "SATimestamp"],
                "timesleep"     : [self.ui.SAtimesleep2, "SASleep"],
                "timesleepRB"   : [self.ui.SAtimesleepRB2, "SASleep"],
                "filename"      : [None, "SAFileName"],
                "enabled"       : [None, "SAEnabled"],
                }
                self.SATab2 = LiberaTab(SATab2Widgets)

                # Set FA tab
                FATab1Widgets = {
                "tabname"       : "FAXZVolt",
                "plot1"         : [self.ui.FAplotA1, "XPosFA","ZPosFA"],
                "plot2"         : [self.ui.FAplotA2, "VaFA","VbFA","VcFA","VdFA"],
                "start"         : [self.ui.FAstart1, "FAAcquire"], 
                "stop"          : [None, None],
                "save"          : [self.ui.FAsave1, ACTIVE_WIDGET],
                "resetPM"       : [None, None],
                "timestamp"     : [None, None],
                "samples"       : [self.ui.FANSamples1, "FANSamples"],
                "samplesRB"     : [self.ui.FANSamplesRB1, "FANSamples"],
                "singleLoop"    : [None, None],
                }
                self.FATab1 = LiberaTab(FATab1Widgets)

                FATab2Widgets = {
                "tabname"       : "FAQSum",
                "plot1"         : [self.ui.FAplotB1, "QuadFA"],
                "plot2"         : [self.ui.FAplotB2, "SumFA"],
                "start"         : [self.ui.FAstart2, "FAAcquire"],
                "stop"          : [None, None],
                "save"          : [self.ui.FAsave2, ACTIVE_WIDGET],
                "resetPM"       : [None, None],
                "timestamp"     : [None, None],
                "samples"       : [self.ui.FANSamples2, "FANSamples"],
                "samplesRB"     : [self.ui.FANSamplesRB2, "FANSamples"],
                "singleLoop"    : [None, None],
                }
                self.FATab2 = LiberaTab(FATab2Widgets)

        def connectLibera(self, dev_name):
            """This function will connect all the window components to the libera received as
            parameter. This parameter may be an integer (hence meaning a libera number, from
            which we'll get the underlying device server) or a string (meaning we want to
            connect directly to the python device server)"""

            dsCppNameBack = self.dsCppName
            dsPyNameBack = self.dsPyName
            self.dsCppName = ""
            self.dsPyName  = ""

            try:
                # Connect to the Device Server and check its state, keep backup of the previous dp; in
                # case of any problem, we'll keep connected to it.
                self.dsPyName = dev_name
                windowTitle = self.dsPyName
                dpBack = self.dp
                self.dp = PyTango.DeviceProxy(self.dsPyName)
                self.dsCppName = self.dp.read_attribute("Device").value
                if self.dsCppName == "":
                    QtGui.QMessageBox.warning(self,
                        self.tr("Device server not located"),
                        self.tr("Unable to find out which underlying cpp device server is serving this python device server. Please, check \"CppDS\" class property on tango database for \"LiberaAcquisator\" class for " + "\"" + self.dsPyName + "\""))
                    return False
                if (self.dp.state() != PyTango.DevState.ON):
                    a = QtGui.QMessageBox.question(self, 
                            self.tr("Device server failed"),
                            self.tr("The status of the device server for this libera is NOT ON."
                            " Are you sure you want to continue?"),
                            QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                    if (a == QtGui.QMessageBox.No):
                        self.dsCppName = dsCppNameBack
                        self.dsPyName = dsPyNameBack
                        self.dp = dpBack
                        return False

                # Connect Tango Values for Environment Parameters and Post Mortem configuration (Warning! This may raise exception)
                self.environment.onEPget()
                self.postMortemConfiguration.PMget()

                # Connect hardware values for StatusBar
                self.LiberaStatusBar.connectLibera(self.dsCppName, self.dsPyName)

                # Clear gain schem tab contents and inform it of the ds change
                self.gainScheme.reset(self.dp)

                # Clear log and inform it of the ds change
                self.log.reset(self.dsCppName)

                # Connect tango values for each tab
                self.ADCTab.connectLibera(self.dsPyName, self.dsCppName)
                self.DDTab1.connectLibera(self.dsPyName, self.dsCppName)
                self.DDTab2.connectLibera(self.dsPyName, self.dsCppName)
                self.PMTab1.connectLibera(self.dsPyName, self.dsCppName)
                self.PMTab2.connectLibera(self.dsPyName, self.dsCppName)
                self.SATab1.connectLibera(self.dsPyName, self.dsCppName)
                self.SATab2.connectLibera(self.dsPyName, self.dsCppName)
                self.FATab1.connectLibera(self.dsPyName, self.dsCppName)
                self.FATab2.connectLibera(self.dsPyName, self.dsCppName)

                # Set main window's title
                self.setWindowTitle(windowTitle)

            except PyTango.DevFailed, e:
                QtGui.QMessageBox.critical(None, "Connect to libera" , repr(e))
                self.dsCppName = dsCppNameBack
                self.dsPyName = dsPyNameBack
                self.dp = dpBack
                return False

        def onActionADCTab(self):
                self.ui.tabWidget.setCurrentIndex(0)

        def onActionDDTab1(self):
                self.ui.tabWidget.setCurrentIndex(1)

        def onActionDDTab2(self):
                self.ui.tabWidget.setCurrentIndex(2)

        def onActionPMTab1(self):
                self.ui.tabWidget.setCurrentIndex(3)

        def onActionPMTab2(self):
                self.ui.tabWidget.setCurrentIndex(4)

        def onActionSATab1(self):
                self.ui.tabWidget.setCurrentIndex(5)

        def onActionSATab2(self):
                self.ui.tabWidget.setCurrentIndex(6)

        def onActionFATab1(self):
                self.ui.tabWidget.setCurrentIndex(7)

        def onActionFATab2(self):
                self.ui.tabWidget.setCurrentIndex(8)

        def onActionGain(self):
                self.ui.tabWidget.setCurrentIndex(9)

        def onActionLog(self):
                self.ui.tabWidget.setCurrentIndex(10)

        def onActionConnectToLibera(self):
            db = PyTango.Database()
            deviceList = list(db.get_device_name(SERVER_NAME,CLASS_NAME).value_string)
            name, ok = QtGui.QInputDialog.getItem(self, self.tr("Libera Selection"),
                                            self.tr("Libera device name:"),deviceList)
            if ok:
                self.connectLibera(str(name))

        def onActionSynchronize(self):
            self.synctime.show()

        def onActionLiberaStart(self):
                a = QtGui.QMessageBox.question(self, 
                        self.tr("Libera Start"),
                        self.tr("Are you sure?"),
                        QtGui.QMessageBox.Yes,
                        QtGui.QMessageBox.No)
                if(a == QtGui.QMessageBox.Yes):
                        self.dp.command_inout("LiberaStart")

        def onActionLiberaStop(self):
                a = QtGui.QMessageBox.question(self, 
                        self.tr("Libera Stop"),
                        self.tr("Are you sure?"),
                        QtGui.QMessageBox.Yes,
                        QtGui.QMessageBox.No)
                if(a == QtGui.QMessageBox.Yes):
                        self.dp.command_inout("LiberaStop")
                elif(a == QtGui.QMessageBox.No):
                        pass

        def onActionLiberaRestart(self):
                a = QtGui.QMessageBox.question(self, 
                        self.tr("Libera Restart"),
                        self.tr("Are you sure?"),
                        QtGui.QMessageBox.Yes,
                        QtGui.QMessageBox.No)
                if(a == QtGui.QMessageBox.Yes):
                        self.dp.command_inout("LiberaRestart")
                elif(a == QtGui.QMessageBox.No):
                        pass

        def onActionLiberaReboot(self):
                a = QtGui.QMessageBox.question(self, 
                        self.tr("Libera Reboot. This will take some time"),
                        self.tr("Are you sure?"),
                        QtGui.QMessageBox.Yes,
                        QtGui.QMessageBox.No)
                if(a == QtGui.QMessageBox.Yes):
                        self.dp.command_inout("LiberaReboot")
                elif(a == QtGui.QMessageBox.No):
                        pass

        def onActionLiberaDSInit(self):
                a = QtGui.QMessageBox.question(self, 
                        self.tr("Libera Device server init."),
                        self.tr("Are you sure?"),
                        QtGui.QMessageBox.Yes,
                        QtGui.QMessageBox.No)
                if(a == QtGui.QMessageBox.Yes):
                        self.dp.command_inout("RunDSCommand","init")
                elif(a == QtGui.QMessageBox.No):
                        pass

        def onActionOpen(self):
                # Check we're connected to something
                if (self.dp is None):
                    QtGui.QMessageBox.warning(self,self.tr("Save environment parameters"),
                                                   self.tr("No connection to any libera"))
                    return
                #choose file
                fileName = QtGui.QFileDialog.getOpenFileName(self,
                    self.tr("Open Environment Parameters"), DEFAULT_PATH,
                    self.tr("DAT (*.dat)"))
                if fileName == '':
                    return

                textEdit = self.openFile(fileName)
                aa = string.split(str(textEdit.toPlainText()))
                column0 = list()
                column1 = list()
                for i in range(len(aa)):
                        if((i%2)==0):
                                column0.append(aa[i])
                        if((i%2)==1):
                                column1.append(aa[i])

                numParam = 25
                if (len(column0) != numParam):
                    QtGui.QMessageBox.warning(self, self.tr("Opening File ..."),
                            self.tr("The number of parameters has to be " + repr(numParam)) )
                    return

                # Set data (from File) in the Environment Parameters Box 
                self.environment.EPxoffset.setText(str(column1[0]))
                self.environment.EPzoffset.setText(str(column1[1]))
                self.environment.EPqoffset.setText(str(column1[2]))
                self.environment.EPkx.setText(str(column1[3]))
                self.environment.EPkz.setText(str(column1[4]))
                self.setSwitches(int(column1[5]))
                self.ui.EPgain.setText(str(column1[6]))
                if( int(column1[7]) == 1):
                        self.environment.EPagc.setCheckState(Qt.Qt.Checked)
                else:
                        self.ui.EPagc.setCheckState(Qt.Qt.Unchecked)
                self.environment.EPsetgain() #disable/enable gain depending on agc
                self.environment.EPdsc.setCurrentIndex(int(column1[8]))
                self.environment.EPmode.setCurrentIndex(int(column1[9]))
                self.environment.EPgainlimit.setText(str(column1[10]))
                self.environment.EPxhigh.setText(str(column1[11]))
                self.environment.EPxlow.setText(str(column1[12]))
                self.environment.EPzhigh.setText(str(column1[13]))
                self.environment.EPzlow.setText(str(column1[14]))
                self.environment.EPoverflim.setText(str(column1[15]))
                self.environment.EPoverfdur.setText(str(column1[16]))
                self.environment.EPclocksource.setCurrentIndex(int(column1[17]))
                self.environment.EPswitchdelay.setText(str((column1[18])))
                self.environment.EPofftunemode.setCurrentIndex(int(column1[19]))
                self.environment.EPofftuneunits.setText(str(column1[20]))
                self.environment.EPpmoffset.setText(str(column1[21]))
                self.environment.EPtrigdelay.setText(str(column1[22]))
                if self.hasMAFSupport:
                    self.environment.EPmaflength.setText(str(column1[23]))
                    self.environment.EPmafdelay.setText(str(column1[24]))
                self.environment.EPActivateWarning()

        def openFile(self, fileName):
                fileEnv = QtCore.QFile(fileName)
                if not fileEnv.open( QtCore.QFile.ReadOnly | QtCore.QFile.Text):
                    QtGui.QMessageBox.warning(self, self.tr("Recent Files"),
                            self.tr("Cannot read file %1:\n%2.").arg(fileName).arg(file.errorString()))
                    return
                instr = QtCore.QTextStream(fileEnv)
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                textEdit = QtGui.QTextEdit()
                textEdit.setPlainText(instr.readAll())
                QtGui.QApplication.restoreOverrideCursor()

                return textEdit 


        def onActionSave(self):
                # Check we're connected to something
                if (self.dp is None):
                    QtGui.QMessageBox.warning(self,self.tr("Save environment parameters"),
                                                   self.tr("No connection to any libera"))
                    return

                # Get file name from Save dialog
                fileName = QtGui.QFileDialog.getSaveFileName(self,
                    self.tr("Save Environment Parameters"), DEFAULT_PATH + "EP.dat",
                    self.tr("DAT (*.dat)"))
                if fileName == '':
                    return False

                return self.saveFile(fileName)


        def saveFile(self, fileName):
                """Save configuration of the Libera to a file."""
                confFile = QtCore.QFile(fileName)
                ## I think that is all....
                if not confFile.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
                    QtGui.QMessageBox.warning(self, self.tr("Application"),
                                self.tr("Cannot write file %1:\n%2.").arg(fileName).arg(confFile.errorString()))
                    return False

                outf = QtCore.QTextStream(confFile)
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

                # Save (to File) all data shown in the Environment Parameters Box
                outf << "xoffset        \t"  << self.ui.EPxoffset.text()                << "\n"
                outf << "zoffset        \t"  << self.ui.EPzoffset.text()                << "\n"
                outf << "qoffset        \t"  << self.ui.EPqoffset.text()                << "\n"
                outf << "kx             \t"  << self.ui.EPkx.text()                     << "\n"
                outf << "kz             \t"  << self.ui.EPkz.text()                     << "\n"
                outf << "switches       \t"  << self.getSwitches()                      << "\n"
                outf << "gain           \t"  << self.ui.EPgain.text()                   << "\n"
                outf << "agc            \t"  << self.ui.EPagc.isChecked()               << "\n" 
                outf << "dsc            \t"  << self.ui.EPdsc.currentIndex()            << "\n"
                outf << "mode           \t"  << self.ui.EPmode.currentIndex()           << "\n"
                outf << "gainlimit      \t"  << self.ui.EPgainlimit.text()              << "\n"
                outf << "xhigh          \t"  << self.ui.EPxhigh.text()                  << "\n"
                outf << "xlow           \t"  << self.ui.EPxlow.text()                   << "\n"
                outf << "zhigh          \t"  << self.ui.EPzhigh.text()                  << "\n"
                outf << "zlow           \t"  << self.ui.EPzlow.text()                   << "\n"
                outf << "overflim       \t"  << self.ui.EPoverflim.text()               << "\n"
                outf << "overfdur       \t"  << self.ui.EPoverfdur.text()               << "\n"
                outf << "clocksource    \t"  << self.ui.EPclocksource.currentIndex()    << "\n"
                outf << "switchdelay    \t"  << self.ui.EPswitchdelay.text()            << "\n"
                outf << "offtunemode    \t"  << self.ui.EPofftunemode.currentIndex()    << "\n"
                outf << "offtuneunits   \t"  << self.ui.EPofftuneunits.text()           << "\n"
                outf << "pmoffset       \t"  << self.ui.EPpmoffset.text()               << "\n"
                outf << "trigdelay      \t"  << self.ui.EPtrigdelay.text()              << "\n"
                if self.hasMAFSupport:
                    maflength = self.ui.EPmaflength.text()
                    mafdelay =  self.ui.EPmafdelay.text()
                else:
                    maflength = None
                    mafdelay =  None
                outf << "maflength      \t"  << str(maflength)                          << "\n"
                outf << "mafdelay       \t"  << str(mafdelay)                           << "\n"

                QtGui.QApplication.restoreOverrideCursor()

                return True

        def onActionPrint(self):
                index = self.ui.tabWidget.currentIndex()
                fileName = self.ui.tabWidget.tabText(index)

                if index == 0:
                    self.ui.ADCplot.exportPrint()
                elif index == 1:
                    self.ui.DDplotA1.exportPrint()
                    self.ui.DDplotA2.exportPrint()
                elif index == 2:
                    self.ui.DDplotB1.exportPrint()
                    self.ui.DDplotB2.exportPrint()
                elif index == 3:
                    self.ui.PMplotA1.exportPrint()
                    self.ui.PMplotA2.exportPrint()
                elif index == 4:
                    self.ui.PMplotB1.exportPrint()
                    self.ui.PMplotB2.exportPrint()
                elif index == 5:
                    self.ui.SAplotA1.exportPrint()
                    self.ui.SAplotA2.exportPrint()
                elif index == 6:
                    self.ui.SAplotB1.exportPrint()
                    self.ui.SAplotB2.exportPrint()
                elif index == 7:    
                    self.ui.FAplotA1.exportPrint()
                    self.ui.FAplotA2.exportPrint()
                elif index == 8:
                    self.ui.FAplotB1.exportPrint()
                    self.ui.FAplotB2.exportPrint()
                elif index == 9:
                    self.gainScheme.print_()
                elif index == 10:
                    self.log.print_()
                    pass
                else:
                    QtGui.QMessageBox.warning(self, self.tr("Application"),"Invalid tab")

                return

        def onActionScreenshot(self):
                self.screenshot.show()

        def onActionHelp(self):
            webbrowser.open(DOC_URL)

        def onActionAbout(self):
            self.aboutDialog = QtGui.QDialog()
            uipath = os.path.join(os.path.dirname(__file__), 
                                  "ui", 
                                  "ui_about.ui")
            uic.loadUi(uipath, self.aboutDialog)
            self.aboutDialog.exec_()

        def onActionQuit(self):
            self.close()


class PostMortemConfiguration(QtGui.QDockWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent=parent)
        uipath = os.path.join(os.path.dirname(__file__), 
                              "ui", 
                              "ui_postmortemconfiguration.ui")
        self.ui = uic.loadUi(uipath, self)
        self.parent = parent

        # Get/Set Buttons
        QtCore.QObject.connect(self.ui.buttonPMget, QtCore.SIGNAL("clicked()"), self.PMget)
        QtCore.QObject.connect(self.ui.buttonPMset, QtCore.SIGNAL("clicked()"), self.PMset)

        # EP Get and Set buttons will become red when any EP value changed.
        QtCore.QObject.connect(self.ui.comboPMmode, QtCore.SIGNAL("activated(const int)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.PMxhigh, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.PMxlow, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.PMzhigh, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.PMzlow, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.PMoverflim, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.PMoverfdur, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)

    def PMget(self):
        try:
            attrs_names = ["PMMode", "PMXHigh", "PMXLow", "PMZHigh", "PMZLow", "PMOverflowLimit","PMOverflowDuration"]

            attrs_value_objects = self.parent.dp.read_attributes(attrs_names)
            attrs_values = [ av.value for av in attrs_value_objects ]
            pairs = dict(zip(attrs_names, attrs_values))

            self.ui.comboPMmode.setCurrentIndex(int(pairs["PMMode"]))
            self.ui.PMxhigh.setText(str(pairs["PMXHigh"]))
            self.ui.PMxlow.setText(str(pairs["PMXLow"]))
            self.ui.PMzhigh.setText(str(pairs["PMZHigh"]))
            self.ui.PMzlow.setText(str(pairs["PMZLow"]))
            self.ui.PMoverflim.setText(str(pairs["PMOverflowLimit"]))
            self.ui.PMoverfdur.setText(str(pairs["PMOverflowDuration"]))

            self.EPResetWarning()
        except PyTango.DevFailed, e:
            QtGui.QMessageBox.critical(None, "PMget" , repr(e))
            raise

    def PMset(self):
        if (self.parent.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("Set Post Mortem configuration"),
                                           self.tr("No connection to any libera"))
            return

        try:
            attrs_names = ["PMMode", "PMXHigh", "PMXLow", "PMZHigh", "PMZLow", "PMOverflowLimit","PMOverflowDuration"]

            write_values = [
                (self.ui.comboPMmode.currentIndex(), True),
                (float(self.ui.PMxhigh.text()), True),  # QString -> str
                (float(self.ui.PMxlow.text()), True),
                (float(self.ui.PMzhigh.text()), True),
                (float(self.ui.PMzlow.text()), True),
                (int(self.ui.PMoverflim.text()), True),
                (int(self.ui.PMoverfdur.text()), True),
            ]

            for idx, pair in enumerate(write_values):
                value, success = pair
                if not success: 
                    QtGui.QMessageBox.critical(None, "PMset" , "Invalid %s" % attrs_names[idx])
                    return

            write_values = [item[0] for item in write_values]

            for attr_name, attr_value in [[attrs_names[i],write_values[i]] for i in range(len(attrs_names))]:
                self.parent.dp.write_attribute(attr_name, attr_value)

        except PyTango.DevFailed, e:
            QtGui.QMessageBox.critical(None, "PMset" , repr(e))
        finally:
                self.PMget()
        return

    def EPActivateWarning(self):
        palette = QtGui.QPalette()

        brush = QtGui.QBrush(QtGui.QColor(255,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Button,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Button,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Button,brush)
        self.ui.buttonPMget.setPalette(palette)
        self.ui.buttonPMset.setPalette(palette)

    def EPResetWarning(self):
        palette = QtGui.QPalette()

        brush = QtGui.QBrush(QtGui.QColor(238,238,238))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Button,brush)

        brush = QtGui.QBrush(QtGui.QColor(238,238,238))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Button,brush)

        brush = QtGui.QBrush(QtGui.QColor(238,238,238))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Button,brush)
        self.ui.buttonPMget.setPalette(palette)
        self.ui.buttonPMset.setPalette(palette)


class Environment(QtGui.QDockWidget):

    def __init__(self, parent):      
        QtGui.QWidget.__init__(self, parent=parent)
        uipath = os.path.join(os.path.dirname(__file__),
                              "ui",
                              "ui_environment.ui")
        self.ui = uic.loadUi(uipath, self)
        
        self.parent = parent

        # 'EP' Buttons
        QtCore.QObject.connect(self.ui.EPget    , QtCore.SIGNAL("clicked()"), self.onEPget)
        QtCore.QObject.connect(self.ui.EPset    , QtCore.SIGNAL("clicked()"), self.onEPset)
        QtCore.QObject.connect(self.ui.EPsettime, QtCore.SIGNAL("clicked()"), self.onEPsettime)
        QtCore.QObject.connect(self.ui.EPagc    , QtCore.SIGNAL("clicked()"), self.EPsetgain)

        # EP Get and Set buttons will become red when any EP value changed.
        QtCore.QObject.connect(self.ui.EPzhigh, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPxoffset, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPzoffset, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPqoffset, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPkx, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPkz, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPswitches, QtCore.SIGNAL("activated(const int)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPdsc, QtCore.SIGNAL("activated(const int)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPgain, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPagc, QtCore.SIGNAL("clicked()"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPmode, QtCore.SIGNAL("activated(const int)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPgainlimit, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPxhigh, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPxlow, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPzhigh, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPzlow, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPoverflim, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPoverfdur, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPclocksource, QtCore.SIGNAL("activated(const int)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPswitchdelay, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPofftunemode, QtCore.SIGNAL("activated(const int)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPofftuneunits, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPpmoffset, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPtrigdelay, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPmaflength, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
        QtCore.QObject.connect(self.ui.EPmafdelay, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)

    def onEPget(self):
        """This function gets environment parameters from the hardware. It calls ParamGet of PyDS,
        which will get parameters from CppDS from hardware. This may cause EPGet to throw exceptions,
        so be sure you know how to handle them"""
        try:
                attrs_name = [ "Xoffset","Zoffset", "Qoffset", "Kx", "Kz", "Switches", "Gain",
                        "AGCEnabled", "DSCMode","InterlockMode", "GainLimit", "Xhigh", "Xlow",
                        "Zhigh", "Zlow", "OverflowLimit","OverflowDuration","ExternalSwitching",
                        "SwitchingDelay", "CompensateTune", "OffsetTune", "PMOffset", "ExternalTriggerDelay"]
                self.hasMAFSupport = self.parent.dp.read_attribute("HasMAFSupport").value
                if self.hasMAFSupport:
                    attrs_name.extend(["MAFLength", "MAFDelay"])
                    self.ui.EPmaflength.setEnabled(True)
                    self.ui.EPmafdelay.setEnabled(True)
                else:
                    self.ui.EPmaflength.clear()
                    self.ui.EPmaflength.setEnabled(False)
                    self.ui.EPmafdelay.clear()
                    self.ui.EPmafdelay.setEnabled(False)

                self.parent.dp.command_inout("ParamGet")
                attrs_value_objects = self.parent.dp.read_attributes(attrs_name)
                attrs_values = [ av.value for av in attrs_value_objects ]
                pairs = dict(zip(attrs_name, attrs_values))
                self.ui.EPxoffset.setText(str(pairs["Xoffset"]))
                self.ui.EPzoffset.setText(str(pairs["Zoffset"]))
                self.ui.EPqoffset.setText(str(pairs["Qoffset"]))
                self.ui.EPkx.setText(str(pairs["Kx"]))
                self.ui.EPkz.setText(str(pairs["Kz"]))
                self.setSwitches(int(pairs["Switches"]))
                if int(pairs["AGCEnabled"]):
                    self.ui.EPagc.setCheckState(Qt.Qt.Checked)
                else:
                    self.ui.EPagc.setCheckState(Qt.Qt.Unchecked)
                self.ui.EPgain.setText(str(pairs["Gain"]))
                self.EPsetgain() #enable/disable gain depending on agc
                self.ui.EPdsc.setCurrentIndex(int(pairs["DSCMode"]))
                self.ui.EPclocksource.setCurrentIndex(int(pairs["ExternalSwitching"]))
                self.ui.EPclocksource.setEnabled(True)
                self.ui.EPswitchdelay.setText(str(pairs["SwitchingDelay"]))
                self.ui.EPswitchdelay.setEnabled(True)
                self.ui.EPofftunemode.setCurrentIndex(int(pairs["CompensateTune"]))
                self.ui.EPofftunemode.setEnabled(True)
                self.ui.EPofftuneunits.setText(str(pairs["OffsetTune"]))
                self.ui.EPofftuneunits.setEnabled(True)
                self.ui.EPpmoffset.setText(str(pairs["PMOffset"]))
                self.ui.EPpmoffset.setEnabled(True)
                self.ui.EPtrigdelay.setText(str(pairs["ExternalTriggerDelay"]))
                self.ui.EPtrigdelay.setEnabled(True)
                if self.hasMAFSupport:
                    self.ui.EPmaflength.setText(str(pairs["MAFLength"]))
                    self.ui.EPmaflength.setEnabled(True)
                    self.ui.EPmafdelay.setText(str(pairs["MAFDelay"]))
                    self.ui.EPmafdelay.setEnabled(True)
                self.setInterlockMode(int(pairs["InterlockMode"]))
                self.ui.EPgainlimit.setText(str(pairs["GainLimit"]))
                self.ui.EPxhigh.setText(str(pairs["Xhigh"]))
                self.ui.EPxlow.setText(str(pairs["Xlow"]))
                self.ui.EPzhigh.setText(str(pairs["Zhigh"]))
                self.ui.EPzlow.setText(str(pairs["Zlow"]))
                self.ui.EPoverflim.setText(str(pairs["OverflowLimit"]))
                self.ui.EPoverfdur.setText(str(pairs["OverflowDuration"]))

                self.EPResetWarning()
        except PyTango.DevFailed, e:
                QtGui.QMessageBox.critical(None, "EPget" , repr(e))
                raise

    def onEPset(self):
        if (self.parent.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("Set environment parameters"),
                                           self.tr("No connection to any libera"))
            return

        #This check is no longer done
        #answer = QtGui.QMessageBox.question(self,
                #self.tr("Set environment parameters"),
                #self.tr("This will stop any running acquisition. It will also reinitialize underlying"\
                        #"C++ device server.\nAre you sure you want to continue?"),
                #QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        #if (answer == QtGui.QMessageBox.No):
            #return False

        try:
            attrs_name_sw = [ "Xoffset","Zoffset","Qoffset","Kx", "Kz","InterlockMode","GainLimit","Xhigh","Xlow","Zhigh","Zlow","OverflowLimit","OverflowDuration" ]
            attrs_name_hw = ["Switches","AGCEnabled","Gain","DSCMode","ExternalSwitching", "SwitchingDelay", "CompensateTune","OffsetTune", "PMOffset", "ExternalTriggerDelay"]
            if self.hasMAFSupport:
                attrs_name_hw.extend(["MAFLength","MAFDelay"])

            write_values_sw = [
            self.ui.EPxoffset.displayText(),
            self.ui.EPzoffset.displayText(),
            self.ui.EPqoffset.displayText(),
            self.ui.EPkx.displayText(),
            self.ui.EPkz.displayText(),
            self.getInterlockMode(),
            self.ui.EPgainlimit.displayText(),
            self.ui.EPxhigh.displayText(),
            self.ui.EPxlow.displayText(),
            self.ui.EPzhigh.displayText(),
            self.ui.EPzlow.displayText(),
            self.ui.EPoverflim.displayText(),
            self.ui.EPoverfdur.displayText()
            ]

            write_values_hw = [
            self.getSwitches(),
            (self.ui.EPagc.checkState()==Qt.Qt.Checked),
            self.ui.EPgain.displayText(),
            self.ui.EPdsc.currentIndex(),
            ]

            #if requesting to activate AGC, gain must not be set or an error will occur
            if (self.ui.EPagc.checkState()==Qt.Qt.Checked):
                write_values_hw.remove(self.ui.EPgain.displayText())
                attrs_name_hw.remove("Gain")

            write_values_hw.extend(
                [
                bool(self.ui.EPclocksource.currentIndex()),
                self.ui.EPswitchdelay.displayText(),
                self.ui.EPofftunemode.currentIndex(),
                self.ui.EPofftuneunits.displayText(),
                self.ui.EPpmoffset.displayText(),
                self.ui.EPtrigdelay.displayText()
                ])

            if self.hasMAFSupport:
                write_values_hw.extend(
                    [
                    self.ui.EPmaflength.displayText(),
                    self.ui.EPmafdelay.displayText()
                    ])

            #Now user decided that this is no longer necessary (until he changes his mind again)
            #self.dp.command_inout("ADCStop")
            #self.dp.command_inout("DDStop")

            #read attributes (will be reused to write_attributes)
            attrs_value_objects_sw = self.parent.dp.read_attributes(attrs_name_sw)
            attrs_value_objects_hw = self.parent.dp.read_attributes(attrs_name_hw)

            sw_changed = False #if no changes, nothing will be done

            #---------------------------------------------------------------
            #first step: set sw attributes
            #first of all, determine if something changed and prepare 
            for i in range(len(write_values_sw)):
                oldValue = attrs_value_objects_sw[i].value
                tipo = type(oldValue)
                newValue = tipo(write_values_sw[i])
                if oldValue != newValue:
                    attrs_value_objects_sw[i].value = newValue
                    sw_changed = True

            if sw_changed:
                self.parent.dp.write_attributes([[attrs_name_sw[i],attrs_value_objects_sw[i].value] for i in range(len(attrs_name_sw))])
                self.parent.dp.command_inout("ParamSet") #this forces the writing to cpp ds

            #---------------------------------------------------------------
            #second step: set hw attributes (if we reached here, there were no exception, so OK.
            for i in range (len(write_values_hw)):
                oldAttr = attrs_value_objects_hw[i]
                tipo = type(oldAttr.value)
                newValue = tipo(write_values_hw[i])
                #write attribute only if really changed
                if oldAttr.value != newValue:
                    self.parent.dp.write_attribute(attrs_name_hw[i],newValue)

            #everything seems to have worked correctly, so reset warning
            self.EPResetWarning()

        except PyTango.DevFailed, e:
            QtGui.QMessageBox.critical(None, "EPset" , repr(e))
        finally:
                self.onEPget()
        return

    def onEPsettime(self):
            self.settime.connect(self.dp)
            self.settime.show()

    def EPActivateWarning(self):
        palette = QtGui.QPalette()

        brush = QtGui.QBrush(QtGui.QColor(255,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Button,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Button,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Button,brush)
        self.ui.EPget.setPalette(palette)
        self.ui.EPset.setPalette(palette)

    def EPResetWarning(self):
        palette = QtGui.QPalette()

        brush = QtGui.QBrush(QtGui.QColor(238,238,238))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Button,brush)

        brush = QtGui.QBrush(QtGui.QColor(238,238,238))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Button,brush)

        brush = QtGui.QBrush(QtGui.QColor(238,238,238))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Button,brush)
        self.ui.EPget.setPalette(palette)
        self.ui.EPset.setPalette(palette)

    def EPsetgain(self):
            if(self.ui.EPagc.isChecked()):
                    self.ui.EPgain.setEnabled(False)
            else:
                    self.ui.EPgain.setEnabled(True)

    def EPcheckIncompatibility(self):
            # FB: storage or boost?
            if(float(self.ui.EPoverfdur.text()) > OVERF_DUR_MAX):
                    a = QtGui.QMessageBox.warning(self, 
                            self.tr("Incompatible setting"),
                            self.tr("Interlock OverF Dur is greater than 1050.\nCheck it!"))
                    if(a == QtGui.QMessageBox.Ok):
                            return

            if(self.ui.EPdsc.currentIndex() == DSC_AUTO) and (self.ui.EPswitches.currentIndex() != SWITCHES_AUTO):
                    a = QtGui.QMessageBox.question(self, 
                            self.tr("Incompatible setting"),
                            self.tr("DSC is set to AUTO\nSwitch has to be set to AUTO"),
                            QtGui.QMessageBox.Yes,
                            QtGui.QMessageBox.No)
                    if(a == QtGui.QMessageBox.Yes):
                            self.ui.EPswitches.setCurrentIndex(SWITCHES_AUTO)

            if(self.ui.EPswitches.currentIndex() == SWITCHES_DIRECT) and (self.ui.EPdsc.currentIndex() != DSC_OFF):
                    a = QtGui.QMessageBox.question(self, 
                            self.tr("Incompatible setting"),
                            self.tr("Switches is set to DIRECT\nDSC has to be set to OFF"),
                            QtGui.QMessageBox.Yes,
                            QtGui.QMessageBox.No)
                    if(a == QtGui.QMessageBox.Yes):
                            self.ui.EPdsc.setCurrentIndex(DSC_OFF)

    def setSwitches(self, v):
            if v == SWITCH_AUTO:
                    self.ui.EPswitches.setCurrentIndex(1)
            else:
                    self.ui.EPswitches.setCurrentIndex(0)

    def getSwitches(self):
            i = self.ui.EPswitches.currentIndex()
            if i==1:
                    return SWITCH_AUTO
            else:
                    return SWITCH_DIRECT

    def setInterlockMode(self, v):
            if v == 0:
                    self.ui.EPmode.setCurrentIndex(0)
            elif v == 1:
                    self.ui.EPmode.setCurrentIndex(1)
            elif v == 3:
                    self.ui.EPmode.setCurrentIndex(2)
            else:
                    self.ui.EPmode.setCurrentIndex(0)

    def getInterlockMode(self):
            i = self.ui.EPmode.currentIndex()
            if i==0:
                    return 0
            elif i==1:
                    return 1
            elif i==2:
                    return 3
            else:
                    return 0


class LiberaStatusBar(QtGui.QWidget):
    def __init__(self, parent):

        QtGui.QWidget.__init__(self, parent=parent)
        
        uipath = os.path.join(os.path.dirname(__file__),
                              "ui",
                              "ui_statusbar.ui")
        self.ui = uic.loadUi(uipath, self)
        
    def connectLibera(self, cppDevice, pyDevice):
        try:
                attrName = cppDevice +"/HWTemperature"
                self.ui.HwTempLabel.setModel(attrName)
                attrName = cppDevice +"/HWTemperature?configuration=label"
                self.ui.HwTempConfigLabel.setModel(attrName)

                attrName = cppDevice +"/Fan1Speed"
                self.ui.Fan1Label.setModel(attrName)
                attrName = cppDevice +"/Fan1Speed?configuration=label"
                self.ui.Fan1ConfigLabel.setModel(attrName)

                attrName = cppDevice +"/Fan2Speed"
                self.ui.Fan2Label.setModel(attrName)
                attrName = cppDevice +"/Fan2Speed?configuration=label"
                self.ui.Fan2ConfigLabel.setModel(attrName)

                attrName = cppDevice +"/SCPLLStatus"
                self.ui.SCPLLLabel.setModel(attrName)
                attrName = cppDevice +"/SCPLLStatus?configuration=label"
                self.ui.SCPLLConfigLabel.setModel(attrName)

                attrName = cppDevice +"/MCPLLStatus"
                self.ui.MCPLLLabel.setModel(attrName)
                attrName = cppDevice +"/MCPLLStatus?configuration=label"
                self.ui.MCPLLConfigLabel.setModel(attrName)

                attrName = cppDevice +'/PMNotified'
                self.ui.PMFlagLed.setModel(attrName)
                attrName = cppDevice + '/PMNotified?configuration=label'
                self.ui.PMConfigLabel.setModel(attrName)

                attrName = cppDevice +'/State'
                self.ui.LiberaCppStateLED.setModel(attrName)
                attrName = cppDevice + '/State?configuration=label'
                self.ui.LiberaStateConfigLabel.setModel(attrName)

                #connect PyDevice state
                attrName = pyDevice +'/State'
                self.ui.LiberaPyStateLED.setModel(attrName)

                #finally, connect state label and widget
                self.ui.liberaStateLabel.setText(cppDevice)

        except Exception, e:
                raise


class SetTime(QtGui.QDialog):
    def __init__(self, parent):

        QtGui.QDialog.__init__(self, parent=parent)
        uipath = os.path.join(os.path.dirname(__file__),
                              "ui",
                              "ui_settime.ui")
        self.ui = uic.loadUi(uipath, self)
        
        # FB cambiar
        self.ui.MachineTimeLineEdit.setText(str(11))
        self.ui.MachinePhaseLineEdit.setText(str(22))

        QtCore.QObject.connect(self.ui.SetButton, QtCore.SIGNAL("clicked()"), self.Set)

        QtCore.QObject.connect(self.ui.MachineTimeLineEdit , QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MachineTimeLineEdit , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MachineTimeLineEdit , QtCore.SIGNAL("textChanged()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MachineTimeLineEdit , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MachinePhaseLineEdit, QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MachinePhaseLineEdit, QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.YearLineEdit     , QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.YearLineEdit     , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MonthLineEdit    , QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MonthLineEdit    , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.DayLineEdit      , QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.DayLineEdit      , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.HourLineEdit     , QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.HourLineEdit     , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MinuteLineEdit   , QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MinuteLineEdit   , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.SecondLineEdit   , QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.SecondLineEdit   , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)

    def connect(self, dp):
        self.dp = dp

    def UpdateMessage(self):
        # MT:MP:YYYYMMDDhhmm.ss
        v1 = self.ui.MachineTimeLineEdit.text()
        v2 = self.ui.MachinePhaseLineEdit.text()
        v3 = self.ui.YearLineEdit.text()
        v4 = self.ui.MonthLineEdit.text() 
        v5 = self.ui.DayLineEdit.text()
        v6 = self.ui.HourLineEdit.text()
        v7 = self.ui.MinuteLineEdit.text() 
        v8 = self.ui.SecondLineEdit.text() 

        msg = v1+'.'+v2+':'+v3+v4+v5+v6+v7+'.'+v8 

        self.ui.LiberaMessageLineEdit.setText(str(msg)) 

    def Set(self):
        v1 = self.ui.MachineTimeLineEdit.text()
        v2 = self.ui.MachinePhaseLineEdit.text()
        v3 = self.ui.YearLineEdit.text()
        v4 = self.ui.MonthLineEdit.text() 
        v5 = self.ui.DayLineEdit.text()
        v6 = self.ui.HourLineEdit.text()
        v7 = self.ui.MinuteLineEdit.text() 
        v8 = self.ui.SecondLineEdit.text() 
        msg = str(v1+'.'+v2+':'+v3+v4+v5+v6+v7+'.'+v8)
        self.ui.LiberaMessageLineEdit.setText(msg)

        # Check parameters
        answer = QtGui.QMessageBox.Yes
        if ((int(v2)<0) or (int(v2)>95)):
            answer = QtGui.QMessageBox.question(self,
                    self.tr("Machine Phase"),
                    self.tr("Machine Phase exceeds booster units. Are you sure you want to proceed?"),
                    QtGui.QMessageBox.Yes,
                    QtGui.QMessageBox.No)
        try:
            datetime(int(v3),int(v4),int(v4),int(v6),int(v7),int(v8))
        except ValueError:
            answer = QtGui.QMessageBox.warning(self,
                    self.tr("Invalid date"),
                    self.tr("The date is invalid. Please enter it again."),
                    QtGui.QMessageBox.Ok)

        #If the answer is Ok or the validation passed, then set libera time
        if (answer == QtGui.QMessageBox.Yes):
            try:
                self.dp.command_inout("SetTimeOnNextTrigger",msg)
                self.hide()
            except PyTango.DevFailed, e:
                QtGui.QMessageBox.critical(None, "EPget" , repr(e))

    def GetGMtime(self):
        t = time.gmtime()

        self.ui.YearLineEdit.setText(str("%04.0f" %t.tm_year)) 
        self.ui.MonthLineEdit.setText(str("%02.0f" %t.tm_mon))
        self.ui.DayLineEdit.setText(str("%02.0f" %t.tm_mday))
        self.ui.HourLineEdit.setText(str("%02.0f" %t.tm_hour))
        self.ui.MinuteLineEdit.setText(str("%02.0f" %t.tm_min))
        self.ui.SecondLineEdit.setText(str("%02.0f" %t.tm_sec))

        self.UpdateMessage()

    def showEvent(self, event):
        self.GetGMtime()


class SyncTime(QtGui.QDialog):
    def __init__(self, parent):      
        QtGui.QDialog.__init__(self, parent=parent)
        uipath = os.path.join(os.path.dirname(__file__),
                              "ui",
                              "ui_synchronize.ui")
        self.ui = uic.loadUi(uipath, self)
        
        self.setup()
        QtCore.QObject.connect(self.ui.setButton,      QtCore.SIGNAL("clicked()"), self.setTimes)
        QtCore.QObject.connect(self.ui.clearButton,    QtCore.SIGNAL("clicked()"), self.clearContents)
        QtCore.QObject.connect(self.ui.loadConfButton, QtCore.SIGNAL("clicked()"), self.loadConf)
        QtCore.QObject.connect(self.ui.saveConfButton, QtCore.SIGNAL("clicked()"), self.saveConf)
        QtCore.QObject.connect(self.ui.doneButton,     QtCore.SIGNAL("clicked()"), self.hide)

    def setup(self):
        self.liberaCount = 120  # number of libera units (now hardcoded, but may be useful)
        self.tableCount = 5     # number of available tables to display libera units (now hardcoded)
        if ((self.liberaCount % self.tableCount) != 0):
            QtGui.QMessageBox.critical(None,"SyncTime" , "Num of liberas must be divisible by num of tables")
            return False

        # Set the headers of the tables
        for i in range(1,self.tableCount+1):
            header1 = QtGui.QTableWidgetItem()
            header1.setText("Machine Time")
            getattr(self.ui,"tableWidget"+str(i)).setColumnCount(2)
            getattr(self.ui,"tableWidget"+str(i)).setHorizontalHeaderItem(0,header1)
            header2 = QtGui.QTableWidgetItem()
            header2.setText("Machine Phase")
            getattr(self.ui,"tableWidget"+str(i)).setHorizontalHeaderItem(1,header2)

        # Fill the rows with libera unit number (header) and empty items for cells
        rowsPerTable = self.liberaCount/self.tableCount
        liberaNumber = 1
        for i in range(1,self.tableCount+1):
            for j in range(0,rowsPerTable):
                item = QtGui.QTableWidgetItem()
                item.setText("%03d" % liberaNumber)
                liberaNumber += 1
                getattr(self.ui,"tableWidget"+str(i)).insertRow(j)
                getattr(self.ui,"tableWidget"+str(i)).setVerticalHeaderItem(j,item)
                item = QtGui.QTableWidgetItem()
                item.setCheckState(QtCore.Qt.Unchecked)
                getattr(self.ui,"tableWidget"+str(i)).setItem(j,0,item)
                item = QtGui.QTableWidgetItem()
                getattr(self.ui,"tableWidget"+str(i)).setItem(j,1,item)

        # Force repaint of the tables to adjust sizes
        for i in range(1,self.tableCount+1):
            getattr(self.ui,"tableWidget"+str(i)).resizeRowsToContents()
            getattr(self.ui,"tableWidget"+str(i)).resizeColumnsToContents()

        # Set current time in the system time line edits
        t = time.gmtime()
        self.ui.YearLineEdit.setText(str("%04.0f" %t.tm_year))
        self.ui.MonthLineEdit.setText(str("%02.0f" %t.tm_mon))
        self.ui.DayLineEdit.setText(str("%02.0f" %t.tm_mday))
        self.ui.HourLineEdit.setText(str("%02.0f" %t.tm_hour))
        self.ui.MinuteLineEdit.setText(str("%02.0f" %t.tm_min))
        self.ui.SecondLineEdit.setText(str("%02.0f" %t.tm_sec))

    def setTimeOnNextTrigger(self,dp,MT,MP):
        v1 = self.ui.YearLineEdit.text()
        v2 = self.ui.MonthLineEdit.text() 
        v3 = self.ui.DayLineEdit.text()
        v4 = self.ui.HourLineEdit.text()
        v5 = self.ui.MinuteLineEdit.text() 
        v6 = self.ui.SecondLineEdit.text() 
        dateTime = str(v1+v2+v3+v4+v5+v6)

        try:
            timeInEpoch = float(calendar.timegm(time.strptime(dateTime, '%Y%m%d%H%M%S')))
        except:
            QtGui.QMessageBox.critical(None,"SyncTime","Invalid date")
            return False

        if (timeInEpoch < 0):
            QtGui.QMessageBox.critical(None,"SyncTime","Invalid date. Min date is 19700101000000")
            return False

        try:
            #write attributes and execute command
            dp.write_attribute("MachineTime", float(MT))
            dp.write_attribute("TimePhase",   int(MP))
            dp.write_attribute("SystemTime",  timeInEpoch)
            dp.command_inout("SetTimeOnNextTrigger")
        except PyTango.DevFailed, e:
            QtGui.QMessageBox.critical(None, "SyncTime" , repr(e))
            return False
        except Exception, e:
            QtGui.QMessageBox.critical(None,"SyncTime","Device server failed to execute command SetTimeOnNextTrigger. Unknown reason: " + repr(e))
            return False

        return True #if we reach this point, everything was OK


    def setTimes(self):
        rowsPerTable = self.liberaCount/self.tableCount
        for i in range(1,self.tableCount+1):
            for j in range(0,rowsPerTable):
                if (getattr(self.ui,"tableWidget"+str(i)).item(j,0).checkState() == QtCore.Qt.Checked):
                    liberaNumber = ((i-1) * rowsPerTable) + (j+1)
                    # try to get MachineTime and MachinePhase values for this libera. If error, paint in red
                    try:
                        MachineTime  = int(getattr(self.ui,"tableWidget"+str(i)).item(j,0).text())
                        MachinePhase = int(getattr(self.ui,"tableWidget"+str(i)).item(j,1).text())
                    except ValueError:
                        QtGui.QMessageBox.critical(None,"SyncTime","setTimes: MachineTime or MachinePhase not valid for libera " + str(liberaNumber))
                        getattr(self.ui,"tableWidget"+str(i)).item(j,0).setBackgroundColor(Qt.Qt.red)
                        getattr(self.ui,"tableWidget"+str(i)).item(j,1).setBackgroundColor(Qt.Qt.red)
                        continue
                    # try to get connection to the libera device server
                    try:
                        dsCppName = str("WS/DI-LI/%03d" % liberaNumber)
                        # Connect to the Device Server and check its state
                        dp = PyTango.DeviceProxy(dsCppName)
                        if (dp.state() != PyTango.DevState.ON):
                            QtGui.QMessageBox.warning(self,
                                self.tr("Device server failed"),
                                self.tr("The status of the device server " + dsCppName + " is not ON"))
                            getattr(self.ui,"tableWidget"+str(i)).item(j,0).setBackgroundColor(Qt.Qt.red)
                            getattr(self.ui,"tableWidget"+str(i)).item(j,1).setBackgroundColor(Qt.Qt.red)
                    except PyTango.DevFailed:
                        QtGui.QMessageBox.critical(None,"SyncTime","setTimes: unable to connect to libera device server " + dsCppName)
                        getattr(self.ui,"tableWidget"+str(i)).item(j,0).setBackgroundColor(Qt.Qt.red)
                        getattr(self.ui,"tableWidget"+str(i)).item(j,1).setBackgroundColor(Qt.Qt.red)
                        continue
                    # and finally try to issue the command to the libera device server
                    if (self.setTimeOnNextTrigger(dp,MachineTime, MachinePhase)):
                        getattr(self.ui,"tableWidget"+str(i)).item(j,0).setBackgroundColor(Qt.Qt.green)
                        getattr(self.ui,"tableWidget"+str(i)).item(j,1).setBackgroundColor(Qt.Qt.green)
                    else:
                        getattr(self.ui,"tableWidget"+str(i)).item(j,0).setBackgroundColor(Qt.Qt.red)
                        getattr(self.ui,"tableWidget"+str(i)).item(j,1).setBackgroundColor(Qt.Qt.red)
                else: #it may be in red due to previous set try (the user may have unchecked it)
                    if (getattr(self.ui,"tableWidget"+str(i)).item(j,0).backgroundColor() == Qt.Qt.red):
                        getattr(self.ui,"tableWidget"+str(i)).item(j,0).setBackgroundColor(Qt.Qt.white)
                        getattr(self.ui,"tableWidget"+str(i)).item(j,1).setBackgroundColor(Qt.Qt.white)

    def clearContents(self):
        rowsPerTable = self.liberaCount/self.tableCount
        for i in range(1,self.tableCount+1):
            for j in range(0,rowsPerTable):
                getattr(self.ui,"tableWidget"+str(i)).item(j,0).setCheckState(QtCore.Qt.Unchecked)
                getattr(self.ui,"tableWidget"+str(i)).item(j,0).setText("")
                getattr(self.ui,"tableWidget"+str(i)).item(j,0).setBackgroundColor(Qt.Qt.white)
                getattr(self.ui,"tableWidget"+str(i)).item(j,1).setText("")
                getattr(self.ui,"tableWidget"+str(i)).item(j,1).setBackgroundColor(Qt.Qt.white)

    def saveConf(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self,
            self.tr("Save liberas times configuration"),  DEFAULT_PATH + "LiberasTimes.dat",
            self.tr("DAT (*.dat)"))
        if fileName == '':
            return False
        file = open(fileName,'w')
        line = "# Liberas time configuration file. Format is:\n"
        file.write(line)
        line = "# liberaUnitNumber setOrNot [MachineTime] [MachinePhase]\n"
        file.write(line)
        line = "# setOrNot specifies if the values will finally be set or not to the libera unit. The\n"
        file.write(line)
        line = "# values admitted are 0 (don't set) or 2 (set)\n"
        file.write(line)
        liberaNumber=1
        try:
            for i in range(1,self.tableCount+1):
                for j in range(0,getattr(self.ui,"tableWidget"+str(i)).rowCount()):
                    line =  str(liberaNumber)
                    line += (" " + str(getattr(self.ui,"tableWidget"+str(i)).item(j,0).checkState()))
                    line += (" " + str(getattr(self.ui,"tableWidget"+str(i)).item(j,0).text()))
                    line += (" " + str(getattr(self.ui,"tableWidget"+str(i)).item(j,1).text()) + "\n")
                    liberaNumber += 1
                    file.write(line)
        finally:
            file.close()

    def loadConf(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,
            self.tr("Open liberas times file"), DEFAULT_PATH,
            self.tr("DAT (*.dat)"))
        if fileName == '':
            return
        file = open(fileName,'r')
        try:
            rowsPerTable  = (self.liberaCount/self.tableCount)
            for line in file:
                tokens = line.split()
                if (tokens[0].startswith("#")): #if it's a comment, go for next loop
                    continue
                liberaNumber = int(tokens[0])
                if (liberaNumber > self.liberaCount):
                    QtGui.QMessageBox.critical(None,"SyncTime" , "LoadConf: libera number read from file (" + str(liberaNumber) +") is greater than max number (" + str(self.liberaCount) + ")")
                    return False
                #determine in which table to insert
                insertInTableNum = ((liberaNumber-1) / rowsPerTable) + 1
                #determine in which row to insert
                row = (liberaNumber-1) % rowsPerTable
                getattr(self.ui,"tableWidget"+str(insertInTableNum)).item(row,0).setCheckState(QtCore.Qt.CheckState(int(tokens[1])))
                if (len(tokens) == 4):
                    getattr(self.ui,"tableWidget"+str(insertInTableNum)).item(row,0).setText(tokens[2])
                    getattr(self.ui,"tableWidget"+str(insertInTableNum)).item(row,1).setText(tokens[3])
        except:
            QtGui.QMessageBox.critical(None,"SyncTime","Unable to load configuration file. Please check that it has a valid format.")
            return False
        finally:
            file.close()


class GainScheme(QtGui.QWidget):

    def __init__(self, parent):
       
        QtGui.QWidget.__init__(self, parent=parent)
        uipath = os.path.join(os.path.dirname(__file__),
                              "ui",
                              "ui_gainscheme.ui")
        self.ui = uic.loadUi(uipath, self)
                
        self.ui.textEdit.setUndoRedoEnabled(True)
        self.dp = None
        self.textModified = False
        QtCore.QObject.connect(self.ui.newButton,          QtCore.SIGNAL("clicked()"), self.new)
        QtCore.QObject.connect(self.ui.openButton,         QtCore.SIGNAL("clicked()"), self.open)
        QtCore.QObject.connect(self.ui.saveButton,         QtCore.SIGNAL("clicked()"), self.save)
        QtCore.QObject.connect(self.ui.printButton,        QtCore.SIGNAL("clicked()"), self.print_)
        QtCore.QObject.connect(self.ui.downloadGainButton, QtCore.SIGNAL("clicked()"), self.downloadGain)
        QtCore.QObject.connect(self.ui.uploadGainButton,   QtCore.SIGNAL("clicked()"), self.uploadGain)
        QtCore.QObject.connect(self.ui.textEdit,           QtCore.SIGNAL("textChanged()"), self.textChanged)

    def reset(self, dp):
        self.dp = dp
        self.ui.textEdit.clear()
        self.textModified = False

    def textChanged(self):
        self.textModified = True

    def new(self):
        if (self.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("No connection"),self.tr("No connection to any libera"))
            return False
        if self.textModified:
            answer = QtGui.QMessageBox.question(self,
                    self.tr("New gain scheme"),
                    self.tr("Gain scheme has been changed. Are you sure?"),
                    QtGui.QMessageBox.Yes,
                    QtGui.QMessageBox.No)
            if(answer == QtGui.QMessageBox.No):
                return False
        self.ui.textEdit.clear()
        self.textModified = False

    def open(self):
        if (self.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("No connection"),self.tr("No connection to any libera"))
            return False
        if self.textModified:
            answer = QtGui.QMessageBox.question(self,
                    self.tr("Open gain scheme"),
                    self.tr("Gain scheme has been changed. Are you sure?"),
                    QtGui.QMessageBox.Yes,
                    QtGui.QMessageBox.No)
            if(answer == QtGui.QMessageBox.No):
                return False
        fileName = QtGui.QFileDialog.getOpenFileName(self,
            self.tr("Open gain scheme"), ".", self.tr("CONF (*.conf)"))
        if fileName == '':
            return False

        gainFile = QtCore.QFile(fileName)
        if not gainFile.open( QtCore.QFile.ReadOnly | QtCore.QFile.Text):
            QtGui.QMessageBox.warning(self, self.tr("Open gain scheme"),
                    self.tr("Cannot read file %1:\n%2.").arg(fileName).arg(gainFile.errorString()))
            return False
        inStream = QtCore.QTextStream(gainFile)
        self.ui.textEdit.setPlainText(inStream.readAll())
        self.textModified = False
        gainFile.close()

    def save(self, fileName=None):
        if (self.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("No connection"),self.tr("No connection to any libera"))
            return False
        # Get file name from Save dialog
        if fileName == None:
            fileName = QtGui.QFileDialog.getSaveFileName(self,
                self.tr("Save gain configuration"), GAIN_FILENAME,
                self.tr("CONF (*.conf)"))
            if fileName == '':
                return False

        # Save contents to file
        gainFile = QtCore.QFile(fileName)
        if not gainFile.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
            QtGui.QMessageBox.warning(self, self.tr("Application"),
                        self.tr("Cannot write file %1:\n%2.").arg(fileName).arg(gainFile.errorString()))
            return False

        outStream = QtCore.QTextStream(gainFile)
        outStream << self.ui.textEdit.toPlainText()
        self.textModified = False
        gainFile.close()

    def downloadGain(self):
        #check if we have connection to the libera
        if (self.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("No connection"),self.tr("No connection to any libera"))
            return False
        #check if the file contents have been changed
        if self.textModified:
            answer = QtGui.QMessageBox.question(self,
                    self.tr("Load gain scheme"),
                    self.tr("Gain scheme has been changed. Are you sure?"),
                    QtGui.QMessageBox.Yes,
                    QtGui.QMessageBox.No)
            if(answer == QtGui.QMessageBox.No):
                return False
        #get gain.conf file from the libera
        try:
            self.ui.textEdit.setPlainText(self.dp.command_inout("GainDownload"))
            self.textModified = False
        except PyTango.DevFailed, e:
            QtGui.QMessageBox.critical(None, "downloadGain" , repr(e))
            return False

    def uploadGain(self):
        if (self.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("No connection"),self.tr("No connection to any libera"))
            return False

        try:
            txt = str(self.ui.textEdit.toPlainText())
            if txt == "":
                a = QtGui.QMessageBox.question(self, 
                        self.tr("Empty gain contents"),
                        self.tr("The gain gain config you try to upload is empty."
                        " Are you sure you want to continue?"),
                        QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                if (a == QtGui.QMessageBox.No):
                    return
            self.dp.command_inout("GainUpload",txt)
        except PyTango.DevFailed, e:
            QtGui.QMessageBox.critical(None, "uploadGain" , repr(e))
            return False

    def print_(self,title="Gain"):
        printer = Qt.QPrinter(Qt.QPrinter.HighResolution)
        dialog = Qt.QPrintDialog(printer)
        if dialog.exec_():
            self.ui.textEdit.print_(printer)


class Log(QtGui.QDialog):

    def __init__(self, parent):

        QtGui.QDialog.__init__(self, parent=parent)
        uipath = os.path.join(os.path.dirname(__file__),
                              "ui",
                              "ui_log.ui")
        self.ui = uic.loadUi(uipath, self)
        
        self.dp = None
        QtCore.QObject.connect(self.ui.updateButton,QtCore.SIGNAL("clicked()"), self.update)
        QtCore.QObject.connect(self.ui.saveButton,QtCore.SIGNAL("clicked()"), self.save)
        QtCore.QObject.connect(self.ui.printButton,QtCore.SIGNAL("clicked()"), self.print_)

    def reset(self, deviceName):
        self.dp = PyTango.DeviceProxy(deviceName)
        self.ui.textEdit.clear()

    def update(self):
        if (self.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("No connection"),self.tr("No connection to any libera"))
            return False
        self.ui.textEdit.clear()
        log = self.dp.read_attribute("logs").value
        if log is None: log = []
        for logLine in log:
            self.ui.textEdit.append(logLine)

    def save(self, fileName=None):
        if (self.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("No connection"),self.tr("No connection to any libera"))
            return False
        # Get file name from Save dialog
        if fileName == None:
            fileName = QtGui.QFileDialog.getSaveFileName(self,
                self.tr("Save log into a file"), "libera.log", self.tr("LOG (*.log)"))
            if fileName == '':
                return False

        # Save contents to file
        logFile = QtCore.QFile(fileName)
        if not logFile.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
            QtGui.QMessageBox.warning(self, self.tr("Application"),
                        self.tr("Cannot write file %1:\n%2.").arg(fileName).arg(logFile.errorString()))
            return False

        outStream = QtCore.QTextStream(logFile)
        outStream << self.ui.textEdit.toPlainText()
        self.textModified = False
        logFile.close()

    def print_(self,title="Log"):
        printer = Qt.QPrinter(Qt.QPrinter.HighResolution)
        dialog = Qt.QPrintDialog(printer)
        if dialog.exec_():
            self.ui.textEdit.print_(printer)


def main():
    parser = argparse.get_taurus_parser()
    parser.add_option("-d", "--device-name", action="store", dest="liberaDsName", type="string", help="Libera device name to connect to")
    app = TaurusApplication(sys.argv, cmd_line_parser=parser,
                      app_name="ctdibpm", app_version=__version,
                      org_domain="ALBA", org_name="ALBA")
    options = app.get_command_line_options()
    ui = MainWindow(liberaDeviceName=options.liberaDsName)
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
