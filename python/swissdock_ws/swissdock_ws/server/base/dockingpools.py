'''
Created on Oct 28, 2011

@author: aurelien
'''
from swissdock_ws.server.base.dockingpool import DockingPool

class DockingPools():
    
    dockingPools = None
    
    def __init__(self):
        self.dockingPools = dict()
            
    def isKnown(self, id):
        if id in self.dockingPools:
            return True
        return False
        
    def getDockingPool(self, id):
        if not self.exists(id):
            raise Exception("DockingPool %s not found"%id)
        return self.dockingPools[id]
    
    def exists(self, id):
        if not id in self.dockingPools:
            return False
        return True
    
    def addDockingPool(self, id, dockingPool_p):
        self.dockingPools[id] = dockingPool_p
        return self.dockingPools[id]
    
    def isWaiting(self, dockingPoolID):
        try:
            return self.getDockingPool(dockingPoolID).status == DockingPool.WAITING
        except:
            return False
    
    def getWaitingDockingPoolIDs(self):
        return filter(self.isWaiting, self.dockingPools)
    
    def isRunning(self, dockingPoolID):
        try:
            return self.getDockingPool(dockingPoolID).status == DockingPool.RUNNING
        except:
            return False
    
    def getRunningDockingPoolIDs(self):
        return filter(self.isRunning, self.dockingPools)
    
    
    def isTerminated(self, dockingPoolID):
        try:
            return self.getDockingPool(dockingPoolID).status == DockingPool.TERMINATED
        except:
            return False
    
    def getTerminatedDockingIDs(self):
        return filter(self.isTerminated, self.dockingPools)
    
    def forget(self, dockingPoolID):
        if (self.isKnown(dockingPoolID)):
            for currentDocking in self.getDockingPool(dockingPoolID).dockings:
                currentDocking.forget()
            del self.dockingPools[dockingPoolID]    
    