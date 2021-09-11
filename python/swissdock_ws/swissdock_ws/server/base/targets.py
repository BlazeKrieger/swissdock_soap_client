'''
Created on Oct 31, 2011

@author: aurelien
'''
from swissdock_ws.server.base.target import Target

class Targets():
    
    targets = None
    
    def __init__(self):
        self.targets = dict()
    
    def getTarget(self, id):
        if not id in self.targets:
            raise Exception("Target %s not found"%id)
        return self.targets[id]
    
    def addTarget(self, id, target_p):
        self.targets[id] = target_p
        return self.targets[id]
    
    def isPreparing(self, targetID):
        try:
            return self.getTarget(targetID).status == Target.PREPARING
        except:
            return False
    
    def getPreparingTargetIDs(self):
        return filter(self.isPreparing, self.targets)
    
    def isPrepared(self, targetID):
        try:
            return self.getTarget(targetID).status == Target.PREPARED
        except:
            return False
    
    def getPreparedTargetIDs(self):
        return filter(self.isPrepared, self.targets)
    
    def isCrashed(self, targetID):
        try:
            return self.getTarget(targetID).status == Target.CRASHED
        except:
            return False
    
    def getCrashedTargetIDs(self):
        return filter(self.isCrashed, self.targets)

    def removeTarget(self, targetID):
        self.getTarget(targetID)
        del self.targets[targetID]    