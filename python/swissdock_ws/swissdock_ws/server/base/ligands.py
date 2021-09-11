'''
Created on Oct 31, 2011

@author: aurelien
'''
from swissdock_ws.server.base.ligand import Ligand

class Ligands():
    
    ligands = None
    
    def __init__(self):
        self.ligands = dict()
    
    def getLigand(self, id):
        if not id in self.ligands:
            raise Exception("Ligand %s not found"%id)
        return self.ligands[id]
    
    def addLigand(self, id, ligand_p):
        self.ligands[id] = ligand_p
        return self.ligands[id]
    
    def isPreparing(self, ligandID):
        try:
            return self.getLigand(ligandID).status == Ligand.PREPARING
        except:
            return False
    
    def getPreparingLigandIDs(self):
        return filter(self.isPreparing, self.ligands)
    
    def isPrepared(self, ligandID):
        try:
            return self.getLigand(ligandID).status == Ligand.PREPARED
        except:
            return False
    
    def getPreparedLigandIDs(self):
        return filter(self.isPrepared, self.ligands)
    
    def isCrashed(self, ligandID):
        try:
            return self.getLigand(ligandID).status == Ligand.CRASHED
        except:
            return False
    
    def getCrashedLigandIDs(self):
        return filter(self.isCrashed, self.ligands)
    
    def removeLigand(self, ligandID):
        self.getLigand(ligandID)
        del self.ligands[ligandID]