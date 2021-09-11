'''
Created on Oct 28, 2011

@author: aurelien
'''
from swissdock_ws.server.base.docking import Docking

class Dockings():
    
    dockings = None
    
    def __init__(self):
        self.dockings = dict()
    
    def isKnown(self, id):
        if id in self.dockings:
            return True
        return False
    
    def getDocking(self, id):
        if not id in self.dockings:
            raise Exception("Docking %s not found" % id)
        return self.dockings[id]
    
    def addDocking(self, id, docking_p):
        self.dockings[id] = docking_p
        return self.dockings[id]
    
    def getQueuedDockingIDs(self):
        return dict((k,v) for k, v in self.dockings.items() if v.isQueued())
    
    def getRunningDockingIDs(self):
        return dict((k,v) for k, v in self.dockings.items() if v.isRunning())
    
    def getTerminatedDockingIDs(self):
        return dict((k,v) for k, v in self.dockings.items() if v.isTerminated())
    
    def forget(self, dockingID):
        if (self.isKnown(dockingID)):
            self.getDocking(dockingID).forget()
            del self.dockings[dockingID]
            