#!/usr/bin/python

'''
Created on Jan 27, 2010

@author: aurelien
'''
from swissdock_ws.SOAPpy import SOAPProxy
#from swissdock.swissdockinterface_client import SwissdockClient
from swissdock_ws.client.base.swissdock_client_impl import SwissdockClient
import zlib

#
# Interesting help @
# http://users.skynet.be/pascalbotte/rcx-ws-doc/python.htm  this site has been deprecated
#
class SwissdockClientSOAPpy(SwissdockClient):
    
    def initServer(self, server):
        self.server = SOAPProxy("http://%s"%server)
        print('Initiating connection with servers')

    def isDockingTerminated(self, jobid):
        print('Is docking terminated? ' + self.server.isDockingTerminated(jobID = jobid))
        return self.server.isDockingTerminated(jobID = jobid)

    def getPredictedDocking(self, jobID):
        t = self.server.getPredictedDocking(jobID = jobID)
        toReturn = t['string']
        toReturn = map(lambda x: zlib.decompress(x.decode("base64")), toReturn)
        print('Get predicted docking')
        return toReturn
    
    def prepareTarget(self, targetString):
        targetCompressedString = zlib.compress(targetString).encode("base64")
        toReturn = self.server.prepareTarget(target = targetCompressedString)
        print('Preparing target')
        return toReturn
    
    def isTargetPrepared(self, targetPreparationJobID):
        print('Is target prepared? ' + self.server.isTargetPrepared(jobID = targetPreparationJobID))
        return self.server.isTargetPrepared(jobID = targetPreparationJobID)

    def getPreparedTarget(self, targetPreparationJobID):
        t = self.server.getPreparedTarget(jobID = targetPreparationJobID)
        print('Get prepared targets')
        if t is None:
            return None
        toReturn = t['string']
        toReturn = map(lambda x: zlib.decompress(x.decode("base64")), toReturn)
        print('Decoding prepared targets')
        return toReturn

    def prepareLigand(self, ligandString):
        ligandCompressedString = zlib.compress(ligandString).encode("base64")
        print('Preparing ligand')
        return self.server.prepareLigand(ligand = ligandCompressedString)
    
    def isLigandPrepared(self, ligandPreparationJobID):
        print('Is ligand prepared? ' + self.server.isLigandPrepared(jobID = ligandPreparationJobID))
        return self.server.isLigandPrepared(jobID = ligandPreparationJobID)

    def getPreparedLigand(self, ligandPreparationJobID):
        t = self.server.getPreparedLigand(jobID = ligandPreparationJobID)
        print('Get prepared ligand')
        if t is None:
            return None
        toReturn = t['string']
        toReturn = map(lambda x: zlib.decompress(x.decode("base64")), toReturn)
        print('Decoding prepared ligand')
        return toReturn

    def getNewDockingPool(self): 
        print('Get new docking pool')
        return self.server.getNewDockingPool()
    
    def isDockingPoolTerminated(self, currentPoolID):
        print('Is docking pool terminated?' + self.server.isDockingPoolTerminated(currentPoolID = currentPoolID))
        return self.server.isDockingPoolTerminated(currentPoolID = currentPoolID)

    def getPredictedDockingPool(self, dockingPoolID, mergedock4):
        t = self.server.getPredictedDockingPool(dockingPoolID = dockingPoolID, mergedock4 = mergedock4)
        toReturn = t['string']
        toReturn = map(lambda x: zlib.decompress(x.decode("base64")), toReturn)
        print('Get predicted docking pool')
        return toReturn
    
    def getPredictedDockingPoolFile(self, dockingPoolID, filename, encode):
        raise Exception("Implement getPredictedDockingPoolFile")
        #return self.server.getPredictedDockingPoolFile(dockingPoolID = dockingPoolID, filename = filename, encode = encode)

    def getPredictedDockingAllFiles(self, jobID):
        t = self.server.getPredictedDockingAllFiles(jobID = jobID)
        toReturn = t.decode("base64")
        print('Get all predicted docking files')
        return toReturn


    def getPredictedDockingFile(self, jobID):
        raise Exception("Implement getPredictedDockingFile")
        #t = self.server.getPredictedDocking(jobID = jobID)
        #toReturn = t['string']
        #return toReturn

    def startDocking(self,
                     targetPsf,
                     targetCrd,
                     ligandPdb,
                     ligandRtf,
                     ligandPar,
                     jobName,
                     emailAddress,
                     password,
                     xmin,
                     xmax,
                     ymin,
                     ymax,
                     zmin,
                     zmax,
                     wantedConfs,
                     nbFactsEval,
                     nbSeeds,
                     sdSteps,
                     abnrSteps,
                     clusteringRadius,
                     maxClusterSize,
                     passiveFlexibilityDistance,
                     ignorePocketBias,
                     keepLigandInPlace,
                     dockingPoolID
                     ):
        targetPsfZ = zlib.compress(targetPsf).encode("base64")
        targetCrdZ = zlib.compress(targetCrd).encode("base64")
        print('Encoding targets')
        ligandPdbZ = zlib.compress(ligandPdb).encode("base64")
        ligandRtfZ = map(lambda x: zlib.compress(x).encode("base64"), ligandRtf)
        ligandParZ = map(lambda x: zlib.compress(x).encode("base64"), ligandPar)
        print('Encoding ligand')
        toReturn = self.server.startDocking(targetPsf = targetPsfZ, 
                                            targetCrd = targetCrdZ, 
                                            ligandPdb = ligandPdbZ,
                                            ligandRtf = ligandRtfZ,
                                            ligandPar = ligandParZ,
                                            jobName = jobName,
                                            emailAddress = emailAddress,
                                            password = password,
                                            xmin = xmin,                                 
                                            xmax = xmax,
                                            ymin = ymin,
                                            ymax = ymax,
                                            zmin = zmin,
                                            zmax = zmax,
                                            wantedConfs = wantedConfs,
                                            nbFactsEval = nbFactsEval,
                                            nbSeeds = nbSeeds,
                                            sdSteps = sdSteps,
                                            abnrSteps = abnrSteps,
                                            clusteringRadius = clusteringRadius,
                                            maxClusterSize = maxClusterSize,
                                            passiveFlexibilityDistance = passiveFlexibilityDistance,
                                            ignorePocketBias = ignorePocketBias,
                                            keepLigandInPlace = keepLigandInPlace,
                                            dockingPoolID = dockingPoolID
                                            )
        print('Starting to dock')
        print('targetCrdZ= ' + targetCrdZ)
        print('targetPsfZ= ' + targetPsfZ)
        print('ligandParZ= ' + str(ligandParZ))
        print('ligandPdbZ= ' + ligandPdbZ)
        print('ligandRtfZ= ' + str(ligandRtfZ))
        print('jobName= ' + jobName)
        print('email= ' + emailAddress)
        print('password= ' + password)
        print('xmin= ' + str(xmin))
        print('xmax= ' + str(xmax))
        print('ymin= ' + str(ymin))
        print('ymax= ' + str(ymax))
        print('zmin= ' + str(zmin))
        print('zmax= ' + str(zmax))
        print('wantedConfs= ' + wantedConfs)
        print('nbFactsEval= ' + nbFactsEval)
        print('nbSeeds= ' + nbSeeds)
        print('sdSteps= ' + sdSteps)
        print('abnrSteps= ' + abnrSteps)
        print('clusteringRadius= ' + str(clusteringRadius))
        print('passiveFlexibilityDistance= ' + str(passiveFlexibilityDistance))
        print('ignorePocketBias= ' + str(ignorePocketBias))
        print('keepLigandInPlace= ' + str(keepLigandInPlace))
        print('dockingPoolID= '+ str(dockingPoolID))
        print('ToReturn= ' + str(toReturn))
        return toReturn
    
    def forget(self, jobid):
        self.server.forget(jobID = jobid)


if __name__ == "__main__":
    sdc = SwissdockClientSOAPpy()
    sdc.run()