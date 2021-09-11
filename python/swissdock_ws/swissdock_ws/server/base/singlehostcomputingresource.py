#!/usr/bin/python

'''
Created on Oct 28, 2011

@author: aurelien
'''

import re
import shlex
from subprocess import PIPE
from subprocess import Popen
from swissdock_ws.server.base.computingresource import ComputingResource

class SingleHostComputingResource(ComputingResource):
    
    _ALLOWPOOLEDJOBS = False
        
    def _parseJobID(self, submissionOutput):
        m = re.search(r"<([0-9]+)>",submissionOutput)
        jobID = m.group(1)
        return jobID 

    def _getStatus(self, lsfJobID):
        cmd = "ssh -i %s -p %s %s %s@%s bjobs %s | awk '{getline; print $3 }'" % (self._SSHKEY, self._DESTINATIONPORT, self._SSHOPTIONS, self._USERNAME, self._DESTINATIONIP, lsfJobID) 
        #output = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True).communicate()
        args = shlex.split(cmd)
        process = Popen(args, stdout=PIPE, stderr=PIPE)
        output = process.communicate()        
        self._checkOutput(output)
        toReturn = output[0].rstrip()        
        allowed = [ "DONE", "RUN", "PEND", "EXIT"]
        if not toReturn in allowed:
            self._logMessage("SSH stdout: %s" % output[0])
        if output[1] != "":
            self._logMessage("SSH stderr: %s" % output[1])
        process.stderr.close()
        process.stdout.close()
        return toReturn        

    def isDockingRunning(self, lsfJobID):
        msg = "checking LSF status for docking %s" % lsfJobID
        status = self._getStatus(lsfJobID)
        if status=='RUN':
            msg = "Docking %s still running" % ( lsfJobID )
            self._logMessage(msg)
            #self.sendReport(msg)
            return True    
        self._logMessage("Docking status: job %s terminated" % lsfJobID)
        return False

    def isDockingTerminated(self, lsfJobID):
        msg = "checking LSF status for docking %s" % lsfJobID
        status = self._getStatus(lsfJobID)
        allowed = [ "DONE", "EXIT" ]
        if status in allowed:
            msg = "Docking %s Terminated" % lsfJobID
            self._logMessage(msg)
            #self._master.sendReport(msg)
            return True
        self._logMessage("Docking status: job %s not terminated" % lsfJobID)
        return False     

