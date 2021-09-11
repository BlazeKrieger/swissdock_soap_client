#!/usr/bin/python

'''
Created on Jan 27, 2010

@author: aurelien
'''

import datetime
import zipfile
import os
import smtplib
import random
import string
import re
import tempfile
import sys
from optparse import OptionParser
import time
from swissdock_ws.server.base.prepareligandthread import PrepareLigandThread
from swissdock_ws.server.base.preparetargetthread import PrepareTargetThread
from swissdock_ws.server.base.dockingdispatcherthread import DockingDispatcherThread
from swissdock_ws.server.base.monitordockingthread import MonitorDockingThread
from swissdock_ws.server.base.monitordockingpoolthread import MonitorDockingPoolThread
from swissdock_ws.server.base.dockingpools import DockingPools
from swissdock_ws.server.base.targets import Targets
from swissdock_ws.server.base.ligands import Ligands
from swissdock_ws.server.base.dockings import Dockings
from swissdock_ws.server.base.docking import Docking
from swissdock_ws.server.base.target import Target
from swissdock_ws.server.base.ligand import Ligand
from swissdock_ws.server.base.dockingpool import DockingPool


class SwissdockServer:
    ''' Register new client requests, maintain a list, and retrieve status.
    '''
    _MOL2MMFF = "/usr/local/bioinfo/MMFF-like/mol2-to-MMFFlike.sh"
    _SETUPREC = "/usr/local/bioinfo/setup-for-charmm/eadock_setup_rec_nogbmv2.sh"
    _RANDOMKEYLENGTH = 20

    def _logMessage(self, message):
        message = message.rstrip()
        timeFormat = "%Y/%m/%d %H:%M:%S"
        if message.count("\n") == 0:
            print "%s: %s" % ( datetime.datetime.today().strftime(timeFormat), message)
        else:
            messageLines = message.split("\n")
            print "%s: %s" % ( datetime.datetime.today().strftime(timeFormat), messageLines[0])
            for line in messageLines[1:]:
                print "%s:  %s" % ( datetime.datetime.today().strftime(timeFormat), line)
        
    def _readFile(self, filename):
        f = open (filename)
        toReturn = f.read()
        f.close
        return toReturn
    
    
    def _zipper(self, dir, zip_file):
        zip = zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED)
        root_len = len(os.path.abspath(dir))
        for root, dirs, files in os.walk(dir):
            archive_root = os.path.abspath(root)[root_len:]
            for f in files:
                fullpath = os.path.join(root, f)
                archive_name = os.path.join(archive_root, f)
                zip.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
        zip.close()
        return zip_file
    
    def sendReport(self, subject, content):
        if self._EMAIL == 'none':
            return
        try:
            msg = ("From: %s\r\nTo: %s\r\nSubject: [SwissDrugDesign][SwissDockD] %s\r\n\r\n%s" % (self._EMAIL, self._EMAIL, subject, content))
            server = smtplib.SMTP('localhost')
            server.sendmail(self._EMAIL, self._EMAIL, msg)
            server.quit()
        except Exception, err:
            print 'ERROR: %s\n' % str(err)
            exit(1) 
        
    def prepareLigand(self, ligand):
        ''' Create PDB/RTF/PAR files for the ligand from
        ZincAC or MOL2
        '''
        randomLigandKey = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(self._RANDOMKEYLENGTH))
        toReturn = str(randomLigandKey)
        currentLigand = Ligand()
        currentLigand.query = ligand
        currentLigand.status = Ligand.PREPARING
        self._ligands.addLigand(toReturn, currentLigand)         
        msg = "Ligand %s sent to the setup queue" % randomLigandKey
        self._logMessage(msg)
        return toReturn
    

    def isLigandPrepared(self, jobID):
        msg = "checking ligand setup queue for %s" % jobID
        self._logMessage(msg)
        if self._ligands.isPrepared(jobID):
            msg = "Ligand %s has been setup" % jobID
            self._logMessage(msg)
            return True
        if self._ligands.isCrashed(jobID):
            msg = "Ligand %s setup crashed" % jobID
            self._logMessage(msg)
            return True
        if self._ligands.isPreparing(jobID):
            return False
        return None

    def getPreparedLigand(self, jobID):
        if self._ligands.isPrepared(jobID):
            toReturn = self._ligands.getLigand(jobID).files
            self._ligands.removeLigand(jobID)
            msg = "Ligand %s has been retrieved" % jobID            
        elif self._ligands.isCrashed(jobID):            
            toReturn = self._ligands.getLigand(jobID).msg
            self._ligands.removeLigand(jobID)
            msg = "Ligand %s failed setup log sent" % jobID
        else:
            return None
        self._logMessage(msg)
        return toReturn
    
    
    def prepareTarget(self, target):
        ''' Create PSF/CRD files for the target from
        PDB AC or PDB
        '''
        randomTargetKey = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(self._RANDOMKEYLENGTH))
        toReturn = str(randomTargetKey)
        currentTarget = Target()
        currentTarget.query = target
        currentTarget.status = Target.PREPARING
        self._targets.addTarget(toReturn, currentTarget) 
        msg = "Target %s sent to the setup queue" % randomTargetKey
        self._logMessage(msg)
        return toReturn
    
    def isTargetPrepared(self, jobID):
        msg = "checking target setup queue for %s" % jobID
        self._logMessage(msg)
        if self._targets.isPrepared(jobID):
            msg = "Target %s has been setup" % jobID
            self._logMessage(msg)
            return True
        if self._targets.isCrashed(jobID):
            msg = "Target %s setup crashed" % jobID
            self._logMessage(msg)
            return True        
        if self._targets.isPreparing(jobID):
            return False
        return None

    def getPreparedTarget(self, jobID):
        if self._targets.isPrepared(jobID):
            toReturn = self._targets.getTarget(jobID).files
            self._targets.removeTarget(jobID)
            msg = "Target %s has been retrieved" % jobID            
        elif self._targets.isCrashed(jobID):
            toReturn = [ self._targets.getTarget(jobID).msg[0], self._targets.getTarget(jobID).msg[0]]
            self._targets.removeTarget(jobID)
            msg = "Target %s failed setup log sent" % jobID
        else:
            return None
        self._logMessage(msg)
        return toReturn
    
    def startDocking( self, targetPsf, targetCrd, ligandPdb, ligandRtf, ligandPar,
                      jobName, emailAddress, password, xmin, xmax, ymin, ymax,
                      zmin, zmax, wantedConfs, nbFactsEval, nbSeeds, sdSteps, abnrSteps,
                      clusteringRadius, maxClusterSize, passiveFlexibilityDistance, ignorePocketBias, keepLigandInPlace, dockingPoolID):
        ''' Launch docking and return JobID from
        - ligand files (PDB, RTF, PAR)
        - target files (PSF, CRD, RTF, PAR)
        - job name
        - email address
        - password ?
        '''
        
        #Merge all parameters (take care of the order)
        #$extraFiles = join(" ", $userFiles["par"])." ".join(" ", $userFiles["rtf"]);
        #$output = shell_exec("/usr/local/bioinfo/MMFF-like/merge-toppar.prl merged ".$extraFiles);

        #wantedConfs = 100
        
        # check parameters
        valid_chars = "-_.%s%s" % (string.ascii_letters, string.digits)
        realJobName = ''.join(c for c in jobName if c in valid_chars)
        if emailAddress is not None and not re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", emailAddress):
            self._logMessage("Invalid email address: %s" % emailAddress)
            raise "Invalid email address: %s" % emailAddress
        
        # register in the queuedDocking (which is read by the SDResourceDispatcher)
        parameters = dict ({
                           "jobName" : realJobName, 
                           "emailAddress" : emailAddress, 
                           "password" : password, 
                           "xmin" : xmin, 
                           "xmax" : xmax, 
                           "ymin" : ymin, 
                           "ymax" : ymax, 
                           "zmin" : zmin, 
                           "zmax" : zmax, 
                           "wantedConfs" : wantedConfs, 
                           "nbFactsEval" : nbFactsEval, 
                           "nbSeeds" : nbSeeds, 
                           "sdSteps" : sdSteps, 
                           "abnrSteps" : abnrSteps, 
                           "clusteringRadius" : clusteringRadius, 
                           "maxClusterSize" : maxClusterSize,
                           "passiveFlexibilityDistance" : passiveFlexibilityDistance,
                           "ignorePocketBias" : ignorePocketBias, 
                           "keepLigandInPlace" : keepLigandInPlace,
                           "dockingPoolID" : dockingPoolID
                           })
        
        randomkey = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(self._RANDOMKEYLENGTH))
        directory = tempfile.mkdtemp(prefix="swissdockd_", suffix="_%s"%randomkey, dir=self._TMPDIR)
        currentJobID = os.path.basename(directory)
        os.chmod(directory,  0755)

        currentDocking = self._dockings.addDocking(currentJobID, Docking())
        currentDocking.parameters = parameters
        currentDocking.name = realJobName
        currentDocking.status = Docking.QUEUED
        currentDocking.setTargetPsf(targetPsf)
        currentDocking.setTargetCrd(targetCrd)
        currentDocking.setLigandPdb(ligandPdb)
        currentDocking.setLigandRtf(ligandRtf)
        currentDocking.setLigandPar(ligandPar)
        
        if parameters['dockingPoolID'] is not None:
            if not self._dockingPools.exists(parameters['dockingPoolID']):
                msg = "Unknown docking pool %s" % parameters['dockingPoolID']
                self._logMessage(msg)
                return None
            self._dockingPools.getDockingPool(parameters['dockingPoolID']).dockings.append(currentDocking)                        

        msg = "Docking %s sent to dispatcher" % currentJobID
        self._logMessage(msg)
        return currentJobID
    
    def isDockingRunning(self, currentJobID):
        ''' Check if currentJobID is still running
        '''
        try:
            return self._dockings.getDocking(currentJobID).isRunning()
        except Exception:
            return False
    
    def isDockingKnown(self, jobID):
        return self._dockings.isKnown(jobID) 
    
    def isDockingPoolKnown(self, jobID):
        return self._dockingPools.isKnown(jobID)    
    
    def isDockingTerminated(self, currentJobID):
        ''' Check status of currentJobID
        '''
        return self._dockings.getDocking(currentJobID).isTerminated()

    def isDockingPoolRunning(self, currentPoolID):
        ''' Check if currentJobID is still running
        '''
        return self._dockingPools.isRunning(currentPoolID)
    
    def isDockingPoolTerminated(self, currentPoolID):
        ''' Check if currentJobID is still running
        '''
        return self._dockingPools.isTerminated(currentPoolID)    
        
    def getNewDockingPool(self):
        ''' Return a new docking pool ID
        '''
        dockingPoolID = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(self._RANDOMKEYLENGTH))
        while self._dockingPools.exists(dockingPoolID):
            dockingPoolID = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(self._RANDOMKEYLENGTH))
        self._dockingPools.addDockingPool(dockingPoolID, DockingPool())
        self._dockingPools.getDockingPool(dockingPoolID).status = DockingPool.WAITING
        return dockingPoolID

    def startDockingPool(self, dockingPoolID):
        self._dockingPools.getDockingPool(dockingPoolID).status = DockingPool.RUNNING
    
    def getPredictedDocking(self, currentJobID):
        ''' Retrieve prediction for currentJobID
        '''
        toReturn = []
        if not self._dockings.getDocking(currentJobID).isTerminated():
            return "Job ID %s not found" % ( currentJobID)
        directory = self._dockings.getDocking(currentJobID).localpath
        files = [ "pdb/target.pdb", "pdb/clusters.dock4.pdb"]
        for f in files:
            file = "%s/%s" % (directory, f)
            if os.path.exists(file): 
                toReturn.append(self._readFile(file))
            else:
                toReturn.append("File %s / %s not found"%(currentJobID,f))            
        return toReturn
    
    def getPredictedDockingAllFiles(self, currentJobID):
        ''' Retrieve all files related to currentJobID
        '''
        if not self._dockings.getDocking(currentJobID).isTerminated():
            return "Job ID %s not found" % ( currentJobID)
        directory = self._dockings.getDocking(currentJobID).localpath
        zipFileName = "%s.zip" % directory
        if not os.path.exists(zipFileName):
            self._zipper(directory, zipFileName)
        toReturn = self._readFile(zipFileName)
        return toReturn.encode("base64")
    
    
    def getPredictedDockingFile(self, currentJobID, filename):
        ''' Retrieve prediction file for currentJobID
        '''
        if not self._dockings.getDocking(currentJobID).isTerminated():
            return "Job ID %s not found" % ( currentJobID)
        directory = self._dockings.getDocking(currentJobID).localpath
        realFile = "%s/%s"%(directory,filename)
        if not os.path.exists(realFile):
            return "File %s / %s not found" % ( currentJobID, filename)
        toReturn = self._readFile(realFile) 
        return toReturn 
    
    def getPredictedDockingPool(self, dockingPoolID, mergedock4):
        if not self._dockingPools.isTerminated(dockingPoolID):
            msg = "Docking pool %s not terminated" % dockingPoolID
            self._logMessage(msg)
            return msg
        toReturn = []
        directory = self._dockingPools.getDockingPool(dockingPoolID).localpath
        toReturn.append(self._readFile("%s/pdb/target.pdb"%directory))        
        toReturn.append(self._readFile("%s/pdb/clusters.dock4.pdb"%directory))
        return toReturn        

    def getPredictedDockingPoolFile(self, dockingPoolID, filename):
        ''' Retrieve prediction file for dockingPoolID
        '''
        if not self._dockingPools.isTerminated(dockingPoolID):
            msg = "Docking pool %s not terminated" % dockingPoolID
        directory = self._dockingPools.getDockingPool(dockingPoolID).localpath
        realFile = "%s/%s"%(directory,filename)
        if not os.path.exists(realFile):
            return "File %s / %s not found" % ( dockingPoolID, filename)
        toReturn = self._readFile(realFile) 
        return toReturn 
            
            
    def forget(self, dockingID):
        try:
            self._dockings.forget(dockingID)                        
        except Exception:
            pass
        try:
            self._dockingPools.forget(dockingID)                        
        except Exception:
            pass
            
    def parseArguments(self):
        try:
            parser = OptionParser()                
            #parser.add_option("-i", "--interface", dest="interface", default="", help="restrict the server to incoming requests on the IP address INTERFACE", metavar="INTERFACE")
            parser.add_option("-p", "--port", dest="port", default=self._PORT, help="port to listen to", metavar="PORT")
            parser.add_option("-k", "--key", dest="sshkey", default=self._SSHKEY, help="path to the Swissdock SSH key", metavar="SSHKEY")
            parser.add_option("-v", "--vitalit-ip", dest="vitalitip", default=self._DESTINATIONIP, help="IP of the vital-it server", metavar="SERVERIP")
            parser.add_option("-P", "--vitalit-port", dest="vitalitport", default=self._DESTINATIONPORT, help="Port of SSH daemon listening on the vital-it server", metavar="SERVERPORT")
            parser.add_option("-l", "--logpath", dest="logpath", default=self._LOGPATH, help="path where the swissdock log file will be stored", metavar="LOGPATH")
            parser.add_option("-m", "--email", dest="email", default=self._EMAIL, help="email address to send the usage reports to (none for no reporting)", metavar="EMAIL")
            parser.add_option("-c", "--cache-directory", dest="localcachedirectory", default=self._LOCALCACHEDIRECTORY, help="Path to the local cache directory containing the swissdock facility to be exported on computing resources", metavar="LOCALCACHEDIRECTORY")
            parser.add_option("-C", "--computing-resources", dest="computingresources", default=None, help="Path to a file containing a list of available computing resources. If this parameter is not defined: vital-it, argos and workstations will be used.", metavar="COMPUTINGRESOURCES")
            parser.add_option("-d", "--debug", action="store_true", dest="debug", default=self._DEBUG, help="Enable debug mode: terminated jobs are detected and retrieved locally, but not removed from the computing resource.")            
            (options, args) = parser.parse_args()
            #self.INTERFACE=options.interface
            self._DESTINATIONIP=options.vitalitip
            self._DESTINATIONPORT=int(options.vitalitport)
            self._PORT=int(options.port)
            self._SSHKEY=options.sshkey
            self._LOGPATH=options.logpath
            self._EMAIL=options.email
            self._LOCALCACHEDIRECTORY = options.localcachedirectory
            self._COMPUTINGRESOURCES = options.computingresources
            self._DEBUG = options.debug
        except Exception, err:
            print 'ERROR: %s\n' % str(err)
            exit(1)

    def _resetLogFile(self, signum, frame):
        try:            
            self.LOGFILE = open("%s/swissdockd.log"%self._LOGPATH, 'a', 0)
            sys.stdout = self.LOGFILE
            sys.stderr = self.LOGFILE
            print "Log file created"
        except Exception,err:
            print "Cannot open %s" % self._LOGPATH
            print err

    def start(self):        
        self.parseArguments()
        # start logs
        if self._LOGPATH == "": return
        self._resetLogFile(None, None)        
        self._logMessage("Server starting")
        
        # start listeners       
        self._ligands = Ligands()
        self._targets = Targets()
        self._dockings = Dockings()
        self._dockingPools = DockingPools()             
        
        self._ligandPreparer = PrepareLigandThread(self, self._ligands)
        self._targetPreparer = PrepareTargetThread(self, self._targets)
        self._dockingDispatcher = DockingDispatcherThread(self, self._dockings, self._dockingPools, self._DESTINATIONIP,self._DESTINATIONPORT,self._SSHKEY, self._LOCALCACHEDIRECTORY)
        self._dockingMonitor = MonitorDockingThread(self, self._dockings, self._dockingPools)
        self._dockingPoolMonitor = MonitorDockingPoolThread(self, self._dockings, self._dockingPools)
        
        self._ligandPreparer.daemon = True
        self._targetPreparer.daemon = True
        self._dockingDispatcher.daemon = True
        self._dockingMonitor.daemon = True
        self._dockingPoolMonitor.daemon = True  
        
        self._ligandPreparer.start()
        self._targetPreparer.start()            
        self._dockingMonitor.start()
        self._dockingPoolMonitor.start()
        self._dockingDispatcher.start()

        self._logMessage("Server is ready")
    
    def __init__(self):
        if not os.environ.has_key("SWISSDOCKDTMPDIR"):
            raise Exception("The environment SWISSDOCKDTMPDIR must be defined.")
        self._TMPDIR = os.environ.get("SWISSDOCKDTMPDIR")
        self._PORT=8080
        #self._DESTINATIONIP =  "vit-prd.unil.ch"
        #self._DESTINATIONPORT =  "22"
        self._DESTINATIONIP =  "localhost"
        self._DESTINATIONPORT =  "2022"
        self._SSHKEY="/etc/swissdock/id_dsa"
        self._LOCALCACHEDIRECTORY = "./cache"
        self._LOGPATH="/var/log"
        self._EMAIL="none"
        self._DEBUG=False

        
    def cleanup(self):
        self._logMessage("Exiting")
        self._ligandPreparer.shouldStop = True
        self._TargetPreparer.shouldStop = True
        self._dockingDispatcher.shouldStop = True
        self._dockingMonitor.shouldStop = True
        self._dockingPoolMonitor.shouldStop = True
        self._logMessage("Waiting for termination")
        time.sleep(5)
