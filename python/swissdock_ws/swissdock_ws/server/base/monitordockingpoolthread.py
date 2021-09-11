#!/usr/bin/python

'''
Created on Oct 28, 2011

@author: aurelien
'''
from threading import Thread
import os
import traceback
import random
import string
import tempfile
import zipfile
import shutil
import re
import time
from swissdock_ws.server.base.dockingpool import DockingPool

class MonitorDockingPoolThread(Thread):
    
    def __init__(self, master_p, dockings_p, dockingPools_p):
        Thread.__init__(self, name="monitorDockingPoolThread")
        self._master =  master_p
        self._dockingPools= dockingPools_p
        self._dockings= dockings_p        
        self.shouldStop = False
        self._initCompletedDockingPool()
        self._POLLTIME = 60

    def _initCompletedDockingPool(self):
        try:
            self._logMessage("Initializing completed docking pool list")
            dirs = [name for name in os.listdir(self._master._TMPDIR)
                    if (os.path.isdir(os.path.join(self._master._TMPDIR, name)) and name.startswith("swissdockdMerged_"))]
            for identifier in dirs:
                try:
                    dockingPoolIDFile = open("%s/dockingPoolID"%(os.path.join(self._master._TMPDIR,identifier)),'r')
                    dockingPoolID = dockingPoolIDFile.readline().strip()
                    dockingPoolIDFile.close()
                    self._dockingPools.getDockingPool(dockingPoolID).localpath = "%s/%s" % (self._master._TMPDIR, identifier)
                    self._dockingPools.getDockingPool(dockingPoolID).status = DockingPool.TERMINATED
                    self._logMessage("Found completed docking pool %s in %s"%(dockingPoolID, self._dockingPools.getDockingPool(dockingPoolID).localpath))
                except Exception:
                    msg = "Cannot initialize completed docking pool list in %s/%s"% (self._master._TMPDIR,identifier)
                    self._master.sendReport(msg, msg)
                    self._logMessage(msg)                                        
        except Exception:
            msg = "Cannot initialize completed docking pool list in %s"%self._master._TMPDIR
            self._master.sendReport(msg, msg)
            self._logMessage(msg)
            traceback.print_exc()


    def _logMessage(self, msg):
        self._master._logMessage(msg)

    def _mergeDockingAssays(self, dockingPoolID):
        randomkey = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(self._master._RANDOMKEYLENGTH))
        directory = tempfile.mkdtemp(prefix="swissdockdMerged_", suffix="_%s"%randomkey, dir=self._master._TMPDIR)
        os.mkdir("%s/charmm"%directory)
        os.mkdir("%s/pdb"%directory)
        dockingPoolIDFile = open("%s/dockingPoolID"%(directory),'w')
        dockingPoolIDFile.write(dockingPoolID)
        dockingPoolIDFile.close()
        destFile = open("%s/pdb/clusters.dock4.pdb"%(directory),'w')
        myZipFile = zipfile.ZipFile("%s/charmm.zip"%(directory), "w")
        keepTopPoses = 10
        firstTarget = True
        firstParams = True
        firstChimerax = True
        runningDockings = self._dockingPools.getDockingPool(dockingPoolID).dockings
        filesMap = dict()
        filesMap["charmm"] = [".crd", ".rtf", ".par", "clusters.zip"]
        filesMap["pdb"] = ["clusters.dock4.pdb", "target.pdb"]
        filesMap[""] = ["open.chimerax", "params"]        
        for currentDocking in runningDockings:
            dockingName = currentDocking.name
            subDirectory = currentDocking.localpath
            files = []            
            for subsubdir, fileExts in filesMap.items():
                for fileExt in fileExts:
                    realDir = "%s/%s"%(subDirectory,subsubdir)
                    if os.path.isdir(realDir):
                        addFiles = filter( lambda name: str(name).endswith(fileExt), os.listdir(realDir) )
                        for addFile in addFiles:
                            files.append("%s/%s"%(subsubdir,addFile))
                    else:
                        msg = "Directory %s not found" % realDir
                        self._logMessage(msg) 
            for i in files:
                oldName = "%s/%s"%(subDirectory, i)
                newNameArray = os.path.splitext(i)
                newName = "%s/%s.%s%s"%(directory, newNameArray[0], dockingName, newNameArray[1])                
                shutil.copyfile(oldName, newName)
                if i.startswith("charmm"):
                    myZipFile.write(newName)
                if firstTarget and i == "pdb/target.pdb" :
                    shutil.copyfile(oldName, "%s/%s"%(directory,i))
                    firstTarget = False
                if firstParams and i == "/params" :
                    shutil.copyfile(oldName, "%s/%s"%(directory,i))
                    firstParams = False                    
                if firstChimerax and i == "/open.chimerax" :
                    shutil.copyfile(oldName, "%s/%s"%(directory,i))
                    firstChimerax = False                    
                if i == "pdb/clusters.dock4.pdb":
                    destFile.write("REMARK  Compound: %s\n"%dockingName)
                    ter = 0        
                    f = open(oldName,'r')
                    for line in f.readlines():
                        destFile.write(line)
                        m = re.match(r"TER$",line)
                        if m:
                            ter += 1
                            if ter >= keepTopPoses:
                                break                            
                            else:
                                destFile.write("REMARK  Compound: %s\n"%dockingName)
                    f.close()
        destFile.close()
        myZipFile.close()
        return directory
    
    def _isDockingPoolRunning(self, dockingPoolID):
        return self._dockingPools.get(dockingPoolID).status == DockingPool.RUNNING  
    
    def _isDockingPoolTerminated(self, dockingPoolID):    
        ''' Check whether all dockings assay of a given docking pool are terminated
        '''        
        if not self._dockingPools.isRunning(dockingPoolID):
            msg = "Unknown docking pool %s" % dockingPoolID
            self._logMessage(msg)
            raise Exception(msg)
        allTerminated = True
        if len(self._dockingPools.get(dockingPoolID).dockings) == 0:
            msg = "Docking pool %s is still empty" % dockingPoolID
            self._logMessage(msg)
            return False
        for dockingID in self._dockingPools.get(dockingPoolID).dockings:
            if not self._dockings.isTerminated(dockingID):
                if not self._dockings.isRunning(dockingID):
                    msg = "Docking pool %s contains job %s which is not terminated and not running" % (dockingPoolID, dockingID)
                    self._dockingPools.get(dockingPoolID).dockings.remove(dockingID)
                    if len(self._dockingPools.get(dockingPoolID).dockings) == 0:
                        self._dockingPools.get(dockingPoolID).status = None
                    self._logMessage(msg)
                allTerminated = False
                break
        return allTerminated
        
    def run(self):        
        while (not self.shouldStop) :
            while (len(self._dockingPools.getRunningDockingPoolIDs()) == 0) :
                time.sleep(self._POLLTIME)
            try:
                runningDockingPools = self._dockingPools.getRunningDockingPoolIDs()
                for dockingPoolID in runningDockingPools:
                    allTerminated = True
                    for currentDocking in self._dockingPools.getDockingPool(dockingPoolID).dockings:
                        if not currentDocking.isTerminated():
                            allTerminated = False
                            break
                    if not allTerminated:
                        continue
                    try:
                        self._logMessage("Merging docking assays for %s"%dockingPoolID)
                        directory = self._mergeDockingAssays(dockingPoolID)
                        self._logMessage("Docking assays for %s merged"%dockingPoolID)
                    except:
                        directory = False
                    if not directory:
                        self._dockingPools.getDockingPool(dockingPoolID).status = DockingPool.TERMINATED
                        raise Exception("Error while merging docking assays")
                    else:
                        self._dockingPools.getDockingPool(dockingPoolID).localpath = directory
                        self._dockingPools.getDockingPool(dockingPoolID).status = DockingPool.TERMINATED
                time.sleep(self._POLLTIME)
            except Exception:
                msg = "Merging of docking pool %s failed" % dockingPoolID
                self._master.sendReport(msg, msg)
                self._logMessage(msg)
                traceback.print_exc()

