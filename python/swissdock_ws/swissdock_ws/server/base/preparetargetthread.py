#!/usr/bin/python

'''
Created on Oct 28, 2011

@author: aurelien
'''
from threading import Thread
import time
import urllib
import hashlib
import os
import tempfile
import shlex
from subprocess import Popen, PIPE
import traceback
from swissdock_ws.server.base.target import Target
import re

class PrepareTargetThread(Thread):
    
    def __init__(self, master_p, targets_p):
        Thread.__init__(self, name="prepareTargetThread")
        self._master = master_p
        self._targets = targets_p
        self.shouldStop = False
        self._POLLTIME = 1
        
    def _logMessage(self, msg):
        self._master._logMessage(msg)
    
    def run(self):    
        while (not self.shouldStop) :
            #while (len(self._preparingTarget) == 0) :
            while (len(self._targets.getPreparingTargetIDs()) == 0) :
                time.sleep(self._POLLTIME)
                pass
            preparingTargetList = self._targets.getPreparingTargetIDs()
            self._logMessage("Found %s in the target preparation queue, processing" % len(preparingTargetList))
            #while len(self._targetOrder) > 0:
            for identifier in preparingTargetList:
                target = self._targets.getTarget(identifier)
                #identifier = self._targetOrder.pop(0)
                #target = self._preparingTarget[identifier]
                self._logMessage("Target %s preparation: started" % identifier)
                try:
                    if target.query.count("\n") < 2:
                        self._logMessage("Target %s preparation: reading %s from PDB" % (identifier, target.query))
                        items = target.query.split(":")
                        if len(items) > 2: raise Exception("Incorrect PDB code : %s" % (target.query))
                        if len(items) == 2:
                            items[1] = items[1].strip().upper()
                        url = "http://www.pdb.org/pdb/download/downloadFile.do?fileFormat=pdb&compression=NO&structureId=%s" % items[0]
                        f = urllib.urlopen(url)
                        target.query = f.read()
                        tmpTargetLines = target.query.split("\n")
                        targetLines = []
                        for tmpTargetLine in tmpTargetLines:
                            if (tmpTargetLine[0:4] == "ATOM" or tmpTargetLine[0:6] == "HETATM" ) and tmpTargetLine[17:20] != "HOH":                                                                                                    
                                if len(items) == 1:
                                    targetLines.append("%s\n"%tmpTargetLine)
                                elif tmpTargetLine[21:22] == items[1]:
                                    targetLines.append("%s\n"%tmpTargetLine)
                                    
                        target.query = ''.join(targetLines)
                        
                    else:
                        self._logMessage("Target %s preparation: reading from data structure" % (identifier))
                        
                    directory = "%s/target.%s" % (self._master._TMPDIR, hashlib.sha256(target.query).hexdigest())
                    if not os.path.exists(directory):
                        os.mkdir(directory)
                        tmpFile = tempfile.mkstemp(suffix=".pdb", dir=directory)
                        self._logMessage("Target %s preparation: dumping to file %s" % (identifier, tmpFile[1]))
                        f = os.fdopen(tmpFile[0], "w")
                        f.write(target.query)
                        f.close()
                        self._logMessage("Target %s preparation: converting to CHARMM format" % identifier)
                        #cmd = "%s %s 2>&1 >error.log" % (self._master._SETUPREC, os.path.basename(tmpFile[1]))
                        #output = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True, cwd=directory).communicate()
                        cmd = "%s %s" % (self._master._SETUPREC, os.path.basename(tmpFile[1]))                        
                        args = shlex.split(cmd)
                        process = Popen(args, stdout=PIPE, stderr=PIPE, cwd=directory)
                        output = process.communicate()
                        if output[0] != "":
                            self._logMessage("Target %s preparation: conversion stdout: %s" % (identifier, output[0]))
                        if output[1] != "":
                            self._logMessage("Target %s preparation: conversion stderr: %s" % (identifier, output[1]))
                        process.stderr.close()
                        process.stdout.close()
                    else:
                        self._logMessage("Reading %s from cache" % (identifier))
                        
                    filenames = dict( { "CRD":"system.crd", "PSF":"system.psf" } )
                    
                    fileExist = True
                    for type, filename in filenames.items():
                        if not os.path.isfile("%s/%s"%(directory,filename)):
                            fileExist = False
                            break
                    if not fileExist:
                        lines = open("%s/error.log"%directory, 'r').readlines()
                        for l in lines:                            
                            if re.match(r"Missing TYR coordinates",l):
                                raise Exception("Missing TYR coordinates")
                        raise IOError("system.crd or system.psf not found" )
                        
                    targetFiles = dict()                
                    for type, filename in filenames.items():
                        f = open("%s/%s" %(directory, filename), "r")
                        targetFiles[type] = f.read()
                        f.close()
                    self._logMessage("Target %s preparation: success" % identifier)
                    #self._preparedTarget[identifier] = [ targetFiles["PSF"], targetFiles["CRD"] ]
                    target.files =  [ targetFiles["PSF"], targetFiles["CRD"] ]
                    target.status = Target.PREPARED
                    #del self._preparingTarget[identifier]
                except Exception, e:
                    msg = "Setup of target %s failed in %s: %s" % (identifier, directory, e.args[0]);
                    self._master.sendReport(msg, msg)
                    self._logMessage(msg)
                    #traceback.print_exc()
                    #self._crashedTarget[identifier] = [ msg ]
                    target.status = Target.CRASHED
                    target.msg = [ msg ]
                    #del self._preparingTarget[identifier]
                    