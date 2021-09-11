'''
Created on Jun 16, 2010

@author: aurelien
'''

from swissdock_ws.soaplib.wsgi_soap import SimpleWSGISoapApp
from swissdock_ws.soaplib.service import soapmethod
from swissdock_ws.soaplib.serializers.primitive import Array,Float,Integer,String,Boolean

from wsgiref.simple_server import make_server

import traceback
import inspect
from swissdock_ws.server.base.swissdockserverimpl import SwissdockServer
import zlib
import signal

#
# Should we have swissadme <-> swisadmeserver (adding log+init facilities) <-> swisadme SOAP server (this object) ? 
# or should be log/init facilities embedded here? Or do we even need them ?

class SwissdockInterfaceWrapper(SimpleWSGISoapApp):
    
    # Uncomment the following line to activate it :)
    # This must be set to http://www.w3.org/2001/XMLSchema,
    # otherwise JAX-WS cannot generate the code. 
    #__tns__= "http://www.w3.org/2001/XMLSchema"
    __tns__= "http://swissdock.vital-it.ch/soap/"
    
    def __init__(self):
        super(SwissdockInterfaceWrapper, self).__init__()
        self.si = SwissdockServer()
    
    @soapmethod(String,_returns=String)
    def prepareLigand(self, ligand):
        try:
            ligand = zlib.decompress(ligand.decode("base64"))
            toReturn=self.si.prepareLigand(ligand)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))
        return toReturn
    
    @soapmethod(String,_returns=Boolean)
    def isLigandPrepared(self, jobID):
        if jobID == 0:
            return None
        try:
            toReturn=self.si.isLigandPrepared(jobID)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))            
        return toReturn
    
    @soapmethod(String,_returns=Array(String))
    def getPreparedLigand(self, jobID):
        try:
            toReturn=self.si.getPreparedLigand(jobID)
            t = map(lambda x: zlib.compress(x).encode("base64"), toReturn)
            toReturn = t
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))
        return toReturn
    
    @soapmethod(String,_returns=String)
    def prepareTarget(self, target):
        try:
            target = zlib.decompress(target.decode("base64"))
            toReturn = self.si.prepareTarget(target)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))
        return toReturn
    
    @soapmethod(String,_returns=Boolean)
    def isTargetPrepared(self, jobID):
        if jobID == 0:
            return None
        try:
            toReturn=self.si.isTargetPrepared(jobID)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))
        return toReturn
    
    @soapmethod(String,_returns=Array(String))
    def getPreparedTarget(self, jobID):
        try:
            toReturn=self.si.getPreparedTarget(jobID)
            toReturn = map(lambda x: zlib.compress(x).encode("base64"), toReturn)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))
        return toReturn
    
    @soapmethod(String, String, String, Array(String), Array(String), String, String, String,
                Float, Float, Float, Float, Float, Float,
                Integer, Integer, Integer, Integer, Integer,
                Float, Integer, Float, Boolean, Boolean, String,
                _returns=String)
    def startDocking(self, targetPsf, targetCrd, ligandPdb, ligandRtf, ligandPar,
                      jobName, emailAddress, password, xmin, xmax, ymin, ymax,
                      zmin, zmax, wantedConfs, nbFactsEval, nbSeeds, sdSteps, abnrSteps,
                      clusteringRadius, maxClusterSize, passiveFlexibilityDistance, ignorePocketBias,
                      keepLigandInPlace, dockingPoolID):
        try:
            targetPsf = targetPsf.decode("base64")
            targetCrd = targetCrd.decode("base64")
            ligandPdb = ligandPdb.decode("base64")
            ligandRtf = map(lambda x: x.decode("base64"), ligandRtf)
            ligandPar = map(lambda x: x.decode("base64"), ligandPar)
            toReturn=self.si.startDocking(targetPsf, targetCrd, ligandPdb, ligandRtf, ligandPar,
                      jobName, emailAddress, password, xmin, xmax, ymin, ymax,
                      zmin, zmax, wantedConfs, nbFactsEval, nbSeeds, sdSteps, abnrSteps,
                      clusteringRadius, maxClusterSize, passiveFlexibilityDistance, ignorePocketBias,
                      keepLigandInPlace, dockingPoolID)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))            
        return toReturn

    @soapmethod(String,_returns=Boolean)
    def isDockingRunning(self, jobID):
        try:
            toReturn=self.si.isDockingRunning(jobID)
        except Exception, err:
            self.si._logMessage(str(err))
            #traceback.print_exc()
            return False
        return toReturn
    
    @soapmethod(String,_returns=Boolean)
    def isDockingKnown(self, jobID):
        try:
            toReturn=self.si.isDockingKnown(jobID)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return False
        return toReturn

    @soapmethod(String,_returns=Boolean)
    def isDockingPoolKnown(self, jobID):
        try:
            toReturn=self.si.isDockingPoolKnown(jobID)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return False
        return toReturn
    
    @soapmethod(String,_returns=Boolean)
    def isDockingTerminated(self, jobID):
        try:
            toReturn=self.si.isDockingTerminated(jobID)
        except Exception, err:
            self.si._logMessage(str(err))
            #traceback.print_exc()
            return False
        return toReturn

    @soapmethod(String)
    def startDockingPool(self, dockingPoolID):
        try:
            toReturn = self.si.startDockingPool(dockingPoolID)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))
        return toReturn

    @soapmethod(_returns=String)
    def getNewDockingPool(self):
        try:
            toReturn = self.si.getNewDockingPool()
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))
        return toReturn
    
    @soapmethod(String, _returns=Boolean)
    def isDockingPoolTerminated(self, currentPoolID):
        try:
            toReturn = self.si.isDockingPoolTerminated(currentPoolID)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return False
        return toReturn
    
    @soapmethod(String, _returns=Boolean)
    def isDockingPoolRunning(self, currentPoolID):
        try:
            toReturn = self.si.isDockingPoolRunning(currentPoolID)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return False
        return toReturn
    
    @soapmethod(String, _returns=Array(String))
    def getPredictedDocking(self, jobID):
        try:
            toReturn=self.si.getPredictedDocking(jobID)
            toReturn = map(lambda x: zlib.compress(x).encode("base64"), toReturn)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))
        return toReturn

    @soapmethod(String, _returns=String)
    def getPredictedDockingAllFiles(self, jobID):
        try:
            toReturn=self.si.getPredictedDockingAllFiles(jobID)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))
        return toReturn


    @soapmethod(String, String, _returns=String)
    def getPredictedDockingFile(self, jobID, filename):
        try:
            toReturn=self.si.getPredictedDockingFile(jobID, filename)            
            toReturn = zlib.compress(toReturn).encode("base64")
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))
        return toReturn

    @soapmethod(String, Boolean, _returns=Array(String))
    def getPredictedDockingPool(self, dockingPoolID, mergedock4):
        try:
            toReturn=self.si.getPredictedDockingPool(dockingPoolID, mergedock4)
            toReturn = map(lambda x: zlib.compress(x).encode("base64"), toReturn)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))
        return toReturn
    
    @soapmethod(String, String, _returns=String)
    def getPredictedDockingPoolFile(self, dockingPoolID, filename):
        try:
            toReturn=self.si.getPredictedDockingPoolFile(dockingPoolID, filename)
            toReturn = zlib.compress(toReturn).encode("base64")
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))
        return toReturn

    @soapmethod(String)
    def forget(self, jobID):
        try:
            self.si.forget(jobID)
        except Exception, err:
            self.si._logMessage(str(err))
            traceback.print_exc()
            return "%s raised an error: %s" % (inspect.stack()[0][3], str(err))    

if __name__ == '__main__':
    sd = SwissdockInterfaceWrapper()
    sd.si.start() # parse arguments and stuff...
    # Add sigusr1 log handler
    signal.signal(signal.SIGUSR1, sd.si._resetLogFile)    
    server = make_server('', sd.si._PORT, sd)
    server.serve_forever()
    # http://localhost:8080/wsdl
    
