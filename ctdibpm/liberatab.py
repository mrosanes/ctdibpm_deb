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

import sys, time
from PyQt4 import QtCore, QtGui, Qt
import PyTango
from os import sep


class LiberaTab:

        data_sources = \
            { "ADC" : "adc",
              "DDXZVolt" : "dd",
              "DDQSum" : "dd",
              "PMXZVolt" : "pm", 
              "PMQSum" : "pm",
              "SAXZVolt" : "sa",
              "SAQSum" : "sa"
        }


        def __init__(self, p):
                self.p = p
                self.tabName = p["tabname"]

                # 4-Spectrum Widgets -> Tango Attrs
                self.plot1 = p["plot1"][0]
                self.plot2 = p["plot2"][0]

                self.plot1Attrs = p["plot1"][1:]
                self.plot2Attrs = p["plot2"][1:]

                # Single loop for adc or dd captures
                self.singleLoop = p["singleLoop"][0]

                # Attr for 'save' proposes
                self.timestamp = p["timestamp"][0]

                # Buttons -> Click signal+ method
                self.configureButton("start",self.start)
                self.configureButton("stop",self.stop)
                self.configureButton("save",self.save)
                self.configureButton("resetPM",self.resetPM)

        def configureButton(self, lbl, method):
                if(self.p[lbl][1] != None):
                        QtCore.QObject.connect(self.p[lbl][0], QtCore.SIGNAL("clicked()"), method)

        def connectTangoAttribute(self, dsPyName, lbl):
                #if attribute is not found, then don't try to connect it
                try:
                    tangoWidget = self.p[lbl][0]
                    tangoAttr = self.p[lbl][1]
                except KeyError:
                    print "Attribute %s not found in device %s" % (lbl,dsPyName)
                    return

                if(tangoAttr == None):
                    return

                try:
                        if tangoAttr:
                            attrName = dsPyName +'/'+ tangoAttr
                            tangoWidget.setModel(attrName)

                except Exception, e:
                        print "connectTangoAttribute Exception        -->   ", str(e)
                        raise


        def connectLibera(self, dsPyName, dsCppName):
                try:
                        self.dsPyName  = dsPyName
                        self.dsCppName  = dsCppName
                        self.dp = PyTango.DeviceProxy(self.dsPyName)
                        self.connectLiberaTab()

                        self.connectTangoAttribute(dsPyName, "samples")
                        self.connectTangoAttribute(dsPyName, "samplesRB")
                        self.connectTangoAttribute(dsPyName, "loops")
                        self.connectTangoAttribute(dsPyName, "loopsRB")
                        self.connectTangoAttribute(dsPyName, "triggercounts")
                        self.connectTangoAttribute(dsPyName, "peakA")
                        self.connectTangoAttribute(dsPyName, "peakB")
                        self.connectTangoAttribute(dsPyName, "peakC")
                        self.connectTangoAttribute(dsPyName, "peakD")
                        self.connectTangoAttribute(dsPyName, "timesleep")
                        self.connectTangoAttribute(dsPyName, "timesleepRB")
                        self.connectTangoAttribute(dsPyName, "timestamp")
                        self.connectTangoAttribute(dsPyName, "timestampRB")
                        self.connectTangoAttribute(dsPyName, "firstcount")
                        self.connectTangoAttribute(dsPyName, "lastcount")
                        self.connectTangoAttribute(dsPyName, "decimation")
                        self.connectTangoAttribute(dsPyName, "decimationRB")
                except Exception, e:
                        print "connectLibera Exception        -->   ", str(e)
                        raise

        def save(self):
            device = None
            try:
                #modify device timeout, since this may be a long operation
                old_timeout = self.dp.get_timeout_millis()
                self.dp.set_timeout_millis(25000)
                # Get file name from Save dialog
                file_attr_name = "%sFileName" % self.data_sources[self.tabName]
                defaultName = self.dp.read_attribute(file_attr_name).value
                fileName, ok = QtGui.QInputDialog.getText(None, "File name", "File name:", QtGui.QLineEdit.Normal, defaultName)
                if (not ok or fileName == ''):
                    return False
                fileName = str(fileName) #convert to normal string

                # Call to DS save function
                if(self.dsPyName):
                    self.dp.write_attribute(self.p["filename"][1],str(fileName))
                    # Check if timestamp has to be saved and inform it to the Device server
                    if ( self.timestamp != None ):
                        if(self.timestamp.isChecked()):
                            timeStamp = True
                        else:
                            timeStamp = False
                        self.dp.write_attribute(self.p["timestamp"][1],timeStamp)

                    if (self.p["save"][1] != None): #we're not in SA mode
                        self.dp.command_inout(self.p["save"][1])
            except Exception, e:
                QtGui.QMessageBox.critical(None, self.tabName , repr(e))
                return False
            finally:
                self.dp.set_timeout_millis(old_timeout)

            return True


        def connectLiberaTab(self):
                try:
                        plot1 = []
                        plot2 = []

                        #connect tab1 attributes
                        for i in range(len(self.plot1Attrs)):
                            plot1.append(self.dsPyName +'/'+ self.plot1Attrs[i])
                        self.plot1.setModel(QtCore.QStringList(plot1))

                        #connect tab2 (if it exists) attributes
                        if self.plot2 != None:
                            for i in range(len(self.plot2Attrs)):
                                plot2.append(self.dsPyName +'/'+ self.plot2Attrs[i])
                            self.plot2.setModel(QtCore.QStringList(plot2))
                except Exception, e:
                        print "connectLiberaTab Exception        -->   ", str(e)
                        raise

        def start(self):

                def check_source_enabled():
                    attr_name = self.p["enabled"][1]
                    attr_enabled = PyTango.AttributeProxy(self.dsCppName + "/" + attr_name)
                    if not attr_enabled.read().value:
                        a = QtGui.QMessageBox.question(None, 
                                "Data source not enabled",
                                "This data source is not enabled. Do you want to enabled",
                                QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                        if (a == QtGui.QMessageBox.No):
                            return False
                        else:
                            attr_enabled.write(True)
                    return True


                if(self.dsPyName):
                        try:
                                data_source = self.data_sources[self.tabName]
                                #if ADC or DD acquire, we must say if we want it to stop after
                                #one reading cycle
                                if (data_source in ("adc","dd")):
                                    singleLoop = self.singleLoop.isChecked()
                                    prevTimeout = self.dp.get_timeout_millis()
                                    self.dp.set_timeout_millis(10000)
                                    retries = 0

                                    #Check data source is enabled
                                    if not check_source_enabled():
                                        return False

                                    #Execute command
                                    while (not self.dp.command_inout(self.p["start"][1],singleLoop)):
                                        self.dp.command_inout(self.p["stop"][1])
                                        time.sleep(0.2)
                                        retries += 1
                                        if retries > 10:
                                            QtGui.QMessageBox.warning(None, self.p["tabname"],
                                                "Cannot start acquisition. Max retries reached")
                                            self.dp.set_timeout_millis(prevTimeout)
                                            return False
                                    self.dp.set_timeout_millis(prevTimeout)
                                    return True

                                # if we are in SA mode
                                if (data_source == "sa"):
                                    #Check data source is enabled
                                    if not check_source_enabled():
                                        return False
                                    if not self.save():
                                        return False

                                #if we're treating with FA data, we must increase timeout before executing
                                #the command, since we can easily reach it depending on the length
                                if (data_source == "fa"):
                                    prevTimeout = self.dp.get_timeout_millis()
                                    self.dp.set_timeout_millis(60000)
                                    self.dp.command_inout(self.p["start"][1])
                                    self.dp.set_timeout_millis(prevTimeout)
                                    return True
                                #finally, run standard acquire command on device (only PM is standard).
                                #timeout must be increased since the command may take long
                                self.dp.command_inout(self.p["start"][1])
                                return True
                        except PyTango.DevFailed, e:
                                QtGui.QMessageBox.critical(None, self.tabName , repr(e))

        def stop(self):
                if(self.dsPyName):
                        try:
                                self.dp.command_inout(self.p["stop"][1])
                        except PyTango.DevFailed, e:
                                QtGui.QMessageBox.critical(None, self.tabName , repr(e))

        def resetPM(self):
            if(self.dsPyName):
                try:
                    self.dp.command_inout(self.p["resetPM"][1])
                except PyTango.DevFailed, e:
                    QtGui.QMessageBox.critical(None, self.tabName , repr(e))

        def freeze(self):
            pass

        def restart(self):
            pass