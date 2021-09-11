#!/usr/bin/python

'''
Created on Oct 28, 2011

@author: aurelien
'''
import zlib
import hashlib


class Docking():
        
    status = None
    resource = None
    identifier = None
    parameters = None
    queuingid = None
    localpath = None
    _targetPsfZ = None
    _targetCrdZ = None
    _ligandPdbZ = None
    _ligandRtfZ = None
    _ligandParZ = None
        
    QUEUED = 0
    RUNNING = 1
    TERMINATED = 2

    _compressedStructuresReferenceCounter = dict()
    _compressedStructures = dict()

    def setTargetPsf(self, targetPsfZ_p):
        key = hashlib.sha256(targetPsfZ_p).hexdigest()
        if not key in  self._compressedStructures:
            self._compressedStructures[key] = targetPsfZ_p    
            self._compressedStructuresReferenceCounter[key] = 1
        else:
            self._compressedStructuresReferenceCounter[key] += 1
        self._targetPsfZ = key 
    
    def setTargetCrd(self, targetCrdZ_p):
        key = hashlib.sha256(targetCrdZ_p).hexdigest()
        if not key in  self._compressedStructures:
            self._compressedStructures[key] = targetCrdZ_p    
            self._compressedStructuresReferenceCounter[key] = 1
        else:
            self._compressedStructuresReferenceCounter[key] += 1     
        self._targetCrdZ = key
    
    def setLigandPdb(self, ligandPdbZ_p):
        key = hashlib.sha256(ligandPdbZ_p).hexdigest()
        if not key in  self._compressedStructures:
            self._compressedStructures[key] = ligandPdbZ_p    
            self._compressedStructuresReferenceCounter[key] = 1
        else:
            self._compressedStructuresReferenceCounter[key] += 1           
        self._ligandPdbZ = key
    
    def setLigandRtf(self, ligandRtfZ_p):
        self._ligandRtfZ = list()
        for i in ligandRtfZ_p:
            key = hashlib.sha256(i).hexdigest()
            if not key in  self._compressedStructures:
                self._compressedStructures[key] = i    
                self._compressedStructuresReferenceCounter[key] = 1
            else:
                self._compressedStructuresReferenceCounter[key] += 1           
            self._ligandRtfZ.append(key)
    
    def setLigandPar(self, ligandParZ_p):
        self._ligandParZ = list()
        for i in ligandParZ_p:
            key = hashlib.sha256(i).hexdigest()
            if not key in  self._compressedStructures:
                self._compressedStructures[key] = i    
                self._compressedStructuresReferenceCounter[key] = 1
            else:
                self._compressedStructuresReferenceCounter[key] += 1        
            self._ligandParZ.append(key)

    def getTargetPsf(self):
        return zlib.decompress(self._compressedStructures[self._targetPsfZ])
    
    def getTargetCrd(self):
        return zlib.decompress(self._compressedStructures[self._targetCrdZ])
    
    def getLigandPdb(self):
        return zlib.decompress(self._compressedStructures[self._ligandPdbZ])
    
    def getLigandRtf(self):
        return map(lambda x:  zlib.decompress(self._compressedStructures[x]), self._ligandRtfZ)  
    
    def getLigandPar(self):
        return map(lambda x:  zlib.decompress(self._compressedStructures[x]), self._ligandParZ)
    
    def isRunning(self):
        return self.status == Docking.RUNNING
                
    def isTerminated(self):
        return self.status == Docking.TERMINATED
        
    def isQueued(self):
        return self.status == Docking.QUEUED
                
                
    def _cleanupStructure(self, key):
        if key is None:
            return
        if key in self._compressedStructuresReferenceCounter:
            self._compressedStructuresReferenceCounter[key] -= 1
            if self._compressedStructuresReferenceCounter[key] == 0:
                del self._compressedStructuresReferenceCounter[key]
                if key in self._compressedStructures:
                    del self._compressedStructures[key]
            
    def forget(self):
        self.status = None
        self.resource = None
        self.identifier = None
        self.parameters = None
        self.queuingid = None
        self.localpath = None
        self._cleanupStructure(self._targetPsfZ)
        self._targetPsfZ = None            
        self._cleanupStructure(self._targetCrdZ)
        self._targetCrdZ = None        
        self._cleanupStructure(self._ligandPdbZ)
        self._ligandPdbZ = None
        self._cleanupStructure(self._ligandRtfZ)
        self._ligandRtfZ = None
        self._cleanupStructure(self._ligandParZ)
        self._ligandParZ = None
        # remove references to the structure files