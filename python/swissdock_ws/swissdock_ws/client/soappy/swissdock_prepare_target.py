#!/usr/bin/python

'''
Created on Jan 27, 2010

@author: aurelien
'''
from SOAPpy import SOAPProxy
#from swissdock.swissdockinterface_client import SwissdockClient
from swissdock_ws.client.base.swissdock_client_impl import SwissdockClient

#
# Interesting help @
# http://users.skynet.be/pascalbotte/rcx-ws-doc/python.htm
#
class SwissdockClientSOAPpy(SwissdockClient):
    
    def initServer(self, server):
        self.server = SOAPProxy("http://%s"%server)

    def isDockingTerminated(self, jobid):
        return self.server.isDockingTerminated(jobID = jobid)

    def getPredictedDocking(self, jobID, getPdb, getDock4):
        t = self.server.getPredictedDocking(jobID = jobID, getPdb = getPdb, getDock4 = getDock4)
        toReturn = t['string']
        return toReturn
    
    def prepareTarget(self, targetString):
        toReturn = self.server.prepareTarget(target = targetString)
        return toReturn
    
    def isTargetPrepared(self, targetPreparationJobID):
        return self.server.isTargetPrepared(jobID = targetPreparationJobID)

    def getPreparedTarget(self, targetPreparationJobID):
        t = self.server.getPreparedTarget(jobID = targetPreparationJobID)
        toReturn = t['string']
        return toReturn

    def prepareLigand(self, ligandString):
        return self.server.prepareLigand(ligand = ligandString)
    
    def isLigandPrepared(self, ligandPreparationJobID):
        return self.server.isLigandPrepared(jobID = ligandPreparationJobID)

    def getPreparedLigand(self, ligandPreparationJobID):
        t = self.server.getPreparedLigand(jobID = ligandPreparationJobID)
        toReturn = t['string']
        return toReturn

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
                     ignorePocketBias,
                     keepLigandInPlace
                     ):
        toReturn = self.server.startDocking(
                                            targetPsf = targetPsf, 
                                            targetCrd = targetCrd, 
                                            ligandPdb = ligandPdb,
                                            ligandRtf = ligandRtf,
                                            ligandPar = ligandPar,
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
                                            ignorePocketBias = ignorePocketBias,
                                            keepLigandInPlace = keepLigandInPlace
                                            )
        return toReturn

if __name__ == "__main__":
    sdc = SwissdockClientSOAPpy()
    sdc.run()

