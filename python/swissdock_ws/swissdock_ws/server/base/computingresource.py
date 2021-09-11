#!/usr/bin/python

'''
Created on Oct 28, 2011

@author: aurelien
'''
import shlex
from subprocess import PIPE, Popen
import re
import os
import traceback
from swissdock_ws.server.base.dockingpool import DockingPool
from swissdock_ws.server.base.docking import Docking

class ComputingResource():
    
    _CACHEDIRECTORYNAME = "cache"
    _SSHOPTIONS = "-oStrictHostKeyChecking=no -oControlMaster=no -oForwardX11=no -oForwardX11Trusted=no -oBatchMode=yes"
    _RSYNCOPTIONS = "-az --delete"
    _ALLOWPOOLEDJOBS = True
    isReady = True

    def __init__(self, master_p, dockings_p, dockingPools_p, resourceName_p, username_p, destinationIP_p, destinationPort_p, sshKey_p, tmpDirectory_p, submissionScript_p, localCacheDirectory_p, id_p):        
        self._inititialize(master_p, dockings_p, dockingPools_p, resourceName_p, username_p, destinationIP_p, destinationPort_p, sshKey_p, tmpDirectory_p, submissionScript_p, localCacheDirectory_p, id_p)
 
    def _inititialize(self, master_p, dockings_p, dockingPools_p, resourceName_p, username_p, destinationIP_p, destinationPort_p, sshKey_p, tmpDirectory_p, submissionScript_p, localCacheDirectory_p, id_p):
        self._master = master_p
        self._id = id_p
        self._dockings = dockings_p
        self._dockingPools = dockingPools_p 
        self._RESOURCENAME = resourceName_p
        self._USERNAME = username_p
        self._DESTINATIONIP =  destinationIP_p
        self._DESTINATIONPORT =  destinationPort_p        
        self._SSHKEY = sshKey_p        
        self._TMPDIRECTORY = tmpDirectory_p
        self._SUBMISSIONSCRIPT = submissionScript_p        
        self._LOCALCACHEDIRECTORY = localCacheDirectory_p
        self._REMOTECACHEDIRECTORY = "%s/%s" % (tmpDirectory_p, self._CACHEDIRECTORYNAME)
        self._DEBUG = master_p._DEBUG
        self._updateCache()
        self._updateJobs()
        
    def setAllowPooledJobs(self, boolean_p):
        self._ALLOWPOOLEDJOBS = boolean_p

    def allowPooledJobs(self):
        return self._ALLOWPOOLEDJOBS

    def _logMessage(self, msg):
        self._master._logMessage(msg)
        
    def _parseJobID(self, submissionOutput):
        raise Exception("Implement _parseJobID !")
    
    def checkResource(self):
        cmd = "ssh -i %s -p %s %s %s@%s 'echo $HOSTNAME'" % (self._SSHKEY, self._DESTINATIONPORT, self._SSHOPTIONS, self._USERNAME, self._DESTINATIONIP);
        args = shlex.split(cmd)
        process = Popen(args, stdout=PIPE, stderr=PIPE)
        output = process.communicate()        
        self._checkOutput(output)
        process.stderr.close()
        process.stdout.close()        
    
    def _checkOutput(self, output):
        previous = self.isReady
        self.isReady = True
        if output[1].find("Connection timed out") > 0 or output[1].find("Connection refused") > 0:
            self.isReady = False
            msg = '\n'.join(output) + '\n'.join(traceback.format_stack())            
            self._logMessage(msg) 
            mailreport = "%s" % msg
            self._master.sendReport("Command sent to %s is broken"%self._RESOURCENAME, mailreport)            

        if previous and not self.isReady:
            msg = "%s %s timed out !" % (self.__class__.__name__, self._RESOURCENAME)
            self._logMessage(msg)
            mailreport = "%s" % msg
            self._master.sendReport("Connection to %s is broken"%self._RESOURCENAME, mailreport)

        if not previous and self.isReady:
            msg = "%s %s is back online" %  (self.__class__.__name__, self._RESOURCENAME)
            self._logMessage(msg)
            mailreport = "%s" % msg
            self._master.sendReport("Connection to %s restored"%self._RESOURCENAME, mailreport)
    
    def _updateCache(self):
        msg = "Updating cache for resource %s (%s)" % (self._RESOURCENAME, self.__class__.__name__)
        self._logMessage(msg)
        mailreport = msg
        cmd = "rsync %s %s/ %s@%s:%s/ -e 'ssh -i %s -p %s %s'\n" % (self._RSYNCOPTIONS, self._LOCALCACHEDIRECTORY, self._USERNAME, self._DESTINATIONIP, self._REMOTECACHEDIRECTORY, self._SSHKEY, self._DESTINATIONPORT,self._SSHOPTIONS)
        args = shlex.split(cmd)
        process = Popen(args, stdout=PIPE, stderr=PIPE)
        output = process.communicate()        
        if output[0] != "":
            msg = "Docking preparation: rsync stdout: %s" % output[0]
            self._logMessage(msg)
            mailreport = "%s\r\n%s" % (mailreport, msg)
        if output[1] != "":
            msg = "Docking preparation: rsync stderr: %s" % output[1]
            self._logMessage(msg)
            mailreport = "%s\r\n%s" % (mailreport, msg)
        self._checkOutput(output)
        process.stderr.close()
        process.stdout.close()

    def _updateJobs(self):
        self._logMessage("Checking %s for running jobs..." % self._RESOURCENAME)
        cmd = "ssh %s -i %s -p %s %s@%s \"for i in %s/*/jobid; do echo $i `cat $i` `awk '/^JOBNAME:/ {print $2}' ${i%%jobid}params`; done\"" % (self._SSHOPTIONS, self._SSHKEY, self._DESTINATIONPORT, self._USERNAME, self._DESTINATIONIP, self._TMPDIRECTORY)
        args = shlex.split(cmd)
        process = Popen(args, stdout=PIPE, stderr=PIPE)
        output = process.communicate()        
        self._checkOutput(output)
        if output[1] != "" and output[1].find("No such file or directory") == -1:
            msg = "Computing resource %s initialization: updateJobs failed stderr: %s" % (self._RESOURCENAME, output[1])
            self._logMessage(msg)
        items = output[0].split("\n")
        process.stderr.close()
        process.stdout.close()        
        for item in items:
            m = re.search(r"%s/([^\s*]+)/jobid (.+) (.+)"%self._TMPDIRECTORY,item)
            if m is None:
                continue
            dockingid = m.group(1)
            jobid  = m.group(2)
            name = m.group(3)
            self._dockings.addDocking(dockingid, Docking())
            self._dockings.getDocking(dockingid).queuingid = jobid
            self._dockings.getDocking(dockingid).resource = self._id
            self._dockings.getDocking(dockingid).name = name
            self._dockings.getDocking(dockingid).status = Docking.RUNNING             
            self._logMessage("Found %s, job %s on %s" % (dockingid, jobid, self._RESOURCENAME))
        
        self._logMessage("Checking %s for running docking pools..." % self._RESOURCENAME)
        cmd = "ssh %s -i %s -p %s %s@%s \"for i in %s/*/dockingpoolid; do echo $i `cat $i`; done\"" % (self._SSHOPTIONS, self._SSHKEY, self._DESTINATIONPORT, self._USERNAME, self._DESTINATIONIP, self._TMPDIRECTORY)
        args = shlex.split(cmd)
        process = Popen(args, stdout=PIPE, stderr=PIPE)
        output = process.communicate()
        self._checkOutput(output)
        if output[1] != "" and output[1].find("No such file or directory") == -1:
            msg = "Computing resource %s initialization: updateJobs failed stderr: %s" % (self._RESOURCENAME, output[1])
            self._logMessage(msg)
        items = output[0].split("\n")
        process.stderr.close()
        process.stdout.close()        
        for item in items:
            m = re.search(r"%s/(.+)/dockingpoolid (.+)"%self._TMPDIRECTORY,item)
            if m is None:
                continue
            dockingid = m.group(1)
            dockingPoolID  = m.group(2)
            if self._dockings.isKnown(dockingid) == False:
                continue
            if not self._dockingPools.exists(dockingPoolID) :
                self._dockingPools.addDockingPool(dockingPoolID, DockingPool())
                self._dockingPools.getDockingPool(dockingPoolID).status = DockingPool.WAITING             
            self._dockingPools.getDockingPool(dockingPoolID).dockings.append(self._dockings.getDocking(dockingid))
            self._logMessage("Job %s belongs to docking pool %s" % (dockingid, dockingPoolID))
        waitingDockingPools = self._dockingPools.getWaitingDockingPoolIDs()
        for dockingPoolID in waitingDockingPools:
            self._dockingPools.getDockingPool(dockingPoolID).status = DockingPool.RUNNING


    def submit(self, currentJobID):
        directory = "%s/%s" % (self._master._TMPDIR, currentJobID)
        msg = "Docking preparation: sending files to %s" % self._RESOURCENAME
        self._logMessage(msg)
        mailreport = msg
        cmd = "rsync %s %s %s@%s:%s -e 'ssh -i %s -p %s %s'\n" % (self._RSYNCOPTIONS, directory, self._USERNAME, self._DESTINATIONIP, self._TMPDIRECTORY, self._SSHKEY, self._DESTINATIONPORT, self._SSHOPTIONS)
        args = shlex.split(cmd)
        process = Popen(args, stdout=PIPE, stderr=PIPE)
        output = process.communicate()        
        if output[0] != "":
            msg = "Docking preparation: rsync stdout: %s" % output[0]
            self._logMessage(msg)
            mailreport = "%s\r\n%s" % (mailreport, msg)
        if output[1] != "":
            msg = "Docking preparation: rsync stderr: %s" % output[1]
            self._logMessage(msg)
            mailreport = "%s\r\n%s" % (mailreport, msg)
        self._checkOutput(output)
        process.stderr.close()
        process.stdout.close()
        self._updateCache()
        
        # launch job through LSF
        self._logMessage("Docking preparation: launching job")
        cmd = "ssh -i %s -p %s %s %s@%s 'cd %s/%s && %s/%s'" % (self._SSHKEY, self._DESTINATIONPORT, self._SSHOPTIONS, self._USERNAME, self._DESTINATIONIP, self._TMPDIRECTORY, currentJobID, self._REMOTECACHEDIRECTORY, self._SUBMISSIONSCRIPT);
        args = shlex.split(cmd)
        process = Popen(args, stdout=PIPE, stderr=PIPE)
        output = process.communicate()        
        if output[0] != "":
            jobID = self._parseJobID(output[0])
            msg = "Docking preparation: SSH stdout: %s" % output[0]
            self._logMessage(msg)
            mailreport = "%s\r\n%s" % (mailreport, msg)            
        if output[1] != "":
            msg = "Docking preparation: SSH stderr: %s" % output[1]
            self._logMessage(msg)
            mailreport = "%s\r\n%s" % (mailreport, msg)
        self._checkOutput(output)
        process.stderr.close()
        process.stdout.close()
        msg = "Docking preparation: job %s launched on %s as %s" % (currentJobID, self._RESOURCENAME, jobID)
        self._logMessage(msg)        
        
        cmd = "ssh -i %s -p %s %s %s@%s 'echo %s > %s/%s/jobid'" % (self._SSHKEY, self._DESTINATIONPORT, self._SSHOPTIONS, self._USERNAME, self._DESTINATIONIP, jobID, self._TMPDIRECTORY, currentJobID);
        args = shlex.split(cmd)
        process = Popen(args, stdout=PIPE, stderr=PIPE)
        output = process.communicate()        
        if output[0] != "":
            jobID = self._parseJobID(output[0])
            msg = "Docking preparation: SSH stdout: %s" % output[0]
            self._logMessage(msg)
            mailreport = "%s\r\n%s" % (mailreport, msg)            
        if output[1] != "":
            msg = "Docking preparation: SSH stderr: %s" % output[1]
            self._logMessage(msg)
            mailreport = "%s\r\n%s" % (mailreport, msg)
        self._checkOutput(output)
        process.stderr.close()
        process.stdout.close()        
        mailreport = "%s\r\n%s" % (mailreport, msg)
        self._master.sendReport(msg, mailreport)
        #self._runningDocking[currentJobID] = jobID
        self._dockings.getDocking(currentJobID).queuingid = jobID
        self._dockings.getDocking(currentJobID).status = Docking.RUNNING

    def retrieveDockingLocally(self, dockingID):
        try:
            directory = "%s/%s" % (self._master._TMPDIR, dockingID)
            msg = "retrieving predictions for docking %s in %s" % (dockingID, directory)
            mailReport = msg
            self._logMessage(msg)
            if not os.path.exists(directory):
                os.mkdir(directory)
                msg = "Docking retrieval: temporary directory is %s" % directory 
                self._logMessage(msg)
                mailReport = "%s\r\n%s" % (mailReport, msg)
            error = False # CHECK IF THE PATH HAS BEEN REMOVED FROM VITAL-IT
            cmd = "rsync %s %s@%s:%s/%s/ %s -e 'ssh -i %s -p %s %s'\n" % (self._RSYNCOPTIONS, self._USERNAME, self._DESTINATIONIP, self._TMPDIRECTORY, dockingID, directory, self._SSHKEY, self._DESTINATIONPORT, self._SSHOPTIONS)
            args = shlex.split(cmd)
            process = Popen(args, stdout=PIPE, stderr=PIPE)
            output = process.communicate()
            if output[0] != "":
                msg = "Docking retrieval: rsync stdout: %s" % output[0]
                self._logMessage(msg)
                mailReport = "%s\r\n%s" % (mailReport, msg)
            if output[1] != "":
                m = re.search(r"failed",output[0])
                if m is not None:
                    error = True
                msg = "Docking retrieval: rsync stderr: %s" % output[1]
                self._logMessage(msg)
                mailReport = "%s\r\n%s" % (mailReport, msg)
            self._checkOutput(output)
            process.stderr.close()
            process.stdout.close()            
            if error:
                msg = "Error while retrieving docking %s in %s" % (dockingID, directory)
                self._logMessage(msg)
                self.sendReport(msg, mailReport)
            elif not self._DEBUG:
                cmd = "ssh -i %s -p %s %s %s@%s 'rm -rf %s/%s'" % (self._SSHKEY, self._DESTINATIONPORT, self._SSHOPTIONS, self._USERNAME, self._DESTINATIONIP, self._TMPDIRECTORY, dockingID)
                args = shlex.split(cmd)
                process = Popen(args, stdout=PIPE, stderr=PIPE)
                output = process.communicate()                
                self._checkOutput(output)
                process.stderr.close()
                process.stdout.close()
                return directory
            else:
                msg = "Debug mode enabled, do not supress %s from %s" % (directory, self._RESOURCENAME)
                self._logMessage(msg)
                return directory
        except Exception:
            msg = "Retrieval of docking %s in %s failed" % (dockingID, directory)
            self._master.sendReport(msg, msg)
            self._logMessage(msg)
            traceback.print_exc()

