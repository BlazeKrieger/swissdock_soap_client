#!/usr/bin/python

'''
Created on Oct 28, 2011

@author: aurelien
'''
import re
import shlex
from subprocess import PIPE, Popen
from swissdock_ws.server.base.computingresource import ComputingResource

class SGEComputingResource(ComputingResource):
               
    def _parseJobID(self, submissionOutput):
        m = re.search(r"Your job ([0-9]+) ",submissionOutput)
        jobID = m.group(1)
        return jobID 
         
    def _getStatus(self, JobID):
        cmd = "ssh -i %s -p %s %s %s@%s \"qstat|egrep '^\s*%s'|awk '{print $5}'\"" % (self._SSHKEY, self._DESTINATIONPORT, self._SSHOPTIONS, self._USERNAME, self._DESTINATIONIP, JobID)
        #output = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True).communicate()
        args = shlex.split(cmd)
        process = Popen(args, stdout=PIPE, stderr=PIPE)
        output = process.communicate()
        self._checkOutput(output)
        toReturn = output[0].rstrip()
        allowed = [ "qw", "t", "r", ""]
        if not toReturn in allowed:
            self._logMessage("SSH stdout: %s" % output[0])
        if output[1] != "":
            self._logMessage("SSH stderr: %s" % output[1])
        process.stderr.close()
        process.stdout.close()
        return toReturn        

    def isDockingRunning(self, JobID):
        msg = "checking SGE status for docking %s" % JobID
        status = self._getStatus(JobID)
        if status=='r' or status=='qw':
            msg = "Docking %s still running" % ( JobID )
            self._logMessage(msg)
            #self.sendReport(msg)
            return True    
        self._logMessage("Docking status: job %s terminated" % JobID)
        return False

    def isDockingTerminated(self, JobID):
        msg = "checking SGE status for docking %s" % JobID
        status = self._getStatus(JobID)
        if status=='':
            msg = "Docking %s Terminated" % JobID
            self._logMessage(msg)
            #self._master.sendReport(msg)
            return True
        self._logMessage("Docking status: job %s:%s not terminated" % (self._RESOURCENAME,JobID))
        return False

