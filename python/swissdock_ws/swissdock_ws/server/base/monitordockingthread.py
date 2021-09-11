#!/usr/bin/python

'''
Created on Oct 28, 2011

@author: aurelien
'''
from threading import Thread
import os
import traceback
import time
import re
from swissdock_ws.server.base.docking import Docking
from swissdock_ws.server.base.dockingpool import DockingPool

class MonitorDockingThread(Thread):
    
    def __init__(self, master_p, dockings_p, dockingPools_p):
        Thread.__init__(self, name="monitorDockingThread")
        self._master = master_p
        self._dockings = dockings_p
        self._dockingPools = dockingPools_p
        self._initCompletedDocking()
        self.shouldStop = False
        self._POLLTIME = 60

    def _logMessage(self, msg):
        self._master._logMessage(msg)

    def _initCompletedDocking(self):
        try:
            self._logMessage("Initializing completed docking list")
            dirs = [name for name in os.listdir(self._master._TMPDIR)
                    if (os.path.isdir(os.path.join(self._master._TMPDIR, name)) and name.startswith("swissdockd_"))]
            for identifier in dirs:
                if os.path.exists("%s/%s/eadock3.err"%(self._master._TMPDIR, identifier)):
                    self._dockings.addDocking(identifier, Docking())
                    self._dockings.getDocking(identifier).localpath = "%s/%s" % (self._master._TMPDIR, identifier)
                    self._dockings.getDocking(identifier).name = self.getDockingName(identifier) 
                    self._dockings.getDocking(identifier).status = Docking.TERMINATED
                    self._logMessage("Found completed docking %s in %s"%(identifier, self._dockings.getDocking(identifier).localpath))
                    if os.path.exists("%s/%s/dockingpoolid"%(self._master._TMPDIR, identifier)):
                        lines = open("%s/%s/dockingpoolid"%(self._master._TMPDIR, identifier), "r").readlines()
                        dockingPoolID = lines[0]
                        if not dockingPoolID in self._dockingPools.dockingPools:
                            self._dockingPools.addDockingPool(dockingPoolID, DockingPool())
                            self._dockingPools.getDockingPool(dockingPoolID).dockings.append(self._dockings.getDocking(identifier))
                            self._dockingPools.getDockingPool(dockingPoolID).status = DockingPool.TERMINATED
                        self._logMessage("Completed docking %s was part of %s"%(identifier, dockingPoolID))
                    
        except Exception:
            msg = "Cannot initialize completed docking list in %s" %self._master._TMPDIR
            self._master.sendReport(msg,msg)
            self._logMessage(msg)
            traceback.print_exc()

    def getDockingName(self, dockingID):
        try:
            directory = self._dockings.getDocking(dockingID).localpath
            lines = open("%s/params" %directory, "r").readlines()
            for l in lines:
                m = re.match(r"JOBNAME: (.+)$",l)
                if m:
                    toReturn = m.group(1)
                    return toReturn 
            raise Exception("Job name not found")
        except Exception:
            msg = "Cannot read name for job %s" % dockingID
            self._logMessage(msg)
            traceback.print_exc()
        return "Unkown_name"

    def run(self):        
        while (not self.shouldStop) :
            while (len(self._dockings.getRunningDockingIDs()) == 0) :
                time.sleep(self._POLLTIME)
            try:
                runningDocking = self._dockings.getRunningDockingIDs()
                for dockingID, currentDocking in runningDocking.items():
                    if currentDocking.resource is not None:
                        realRes = self._master._dockingDispatcher._computingResource[currentDocking.resource]
                        if realRes.isDockingTerminated(currentDocking.queuingid):
                            directory = realRes.retrieveDockingLocally(dockingID)
                            if directory is False:
                                raise Exception("Error while retrieving docking assays locally")
                            currentDocking.localpath = directory
                            currentDocking.status = Docking.TERMINATED
                time.sleep(self._POLLTIME)
            except Exception:
                msg = "Retrieval of docking %s failed (queuing system ID: %s)" % (dockingID, currentDocking.queuingid)
                self._master.sendReport(msg, msg)
                self._logMessage(msg)
                traceback.print_exc()

