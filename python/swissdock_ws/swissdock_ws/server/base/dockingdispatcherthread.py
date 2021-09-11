#!/usr/bin/python

'''
Created on Oct 28, 2011

@author: aurelien
'''
from threading import Thread
import fileinput
import re
import traceback
import os
import time
from swissdock_ws.server.base.lsfcomputingresource import LSFComputingResource
from swissdock_ws.server.base.sgecomputingresource import SGEComputingResource
from PyCHARMM.CharmmWrapper import CharmmWrapper
import zlib
from swissdock_ws.server.base.docking import Docking

class DockingDispatcherThread(Thread):
    
    def __init__(self, master_p, dockings_p, dockingPools_p, destinationIp_p, destinationPort_p, sshKey_p, localCacheDirectory_p):                         
        Thread.__init__(self, name="dockingDispatcherThread")
        self._master = master_p
        self._dockings = dockings_p
        self._dockingPools = dockingPools_p
        self._computingResource = list()
        self._localCacheDirectory = localCacheDirectory_p
        self._dockingQueuePollInterval = 10
        self._computingResourcesPollInterval = 600        
        if master_p._COMPUTINGRESOURCES is not None:
            try:
                currentResource = dict()
                for line in fileinput.input(master_p._COMPUTINGRESOURCES):
                    line = line.strip()
                    if line.startswith("#") or line == "":
                        continue
                    newResource = re.match(r"\[(.+)\]", line)
                    if newResource:
                        if len(currentResource) != 0:
                            self._addResource(currentResource)
                            currentResource = dict()
                        currentResource['type'] = newResource.group(1)
                        
                    else:
                        t = re.match(r"(\S+) (.+)", line)
                        if t:
                            currentResource[t.group(1)] = t.group(2) 
                self._addResource(currentResource)
            except Exception:
                msg = "Cannot initialize Computing Resources from %s, using default resources instead" % (master_p._COMPUTINGRESOURCES)
                self._logMessage("%s: %s"%(msg, traceback.print_exc()))
                self._master.sendReport(msg, "%s: %s"%(msg, traceback.print_exc()))
                                            
        if len(self._computingResource) == 0:
            self._computingResource.append(LSFComputingResource(
                                                                master_p,
                                                                self._dockings,
                                                                self._dockingpools,
                                                                "Vital-IT",
                                                                "swissdock",
                                                                "vit-prd.unil.ch",
                                                                "22",
                                                                "/etc/swissdock/id_dsa",
                                                                "/home/swissdock/swissdock/tmp/",
                                                                "submission/launch.frt.prdclst.vital-it.ch",
                                                                self._localCacheDirectory
                                                                ))
            self._computingResource.append(SGEComputingResource(
                                                                master_p,
                                                                self._dockings,
                                                                self._dockingpools,
                                                                "Argos",
                                                                "agrosdid",
                                                                "argos1.unil.ch",
                                                                "22",                                                            
                                                                "/etc/swissdock/id_dsa",
                                                                "/users/agrosdid/swissdock/tmp",
                                                                "submission/launch.argos1.unil.ch",
                                                                self._localCacheDirectory
                                                                ))
            self._computingResource.append(SGEComputingResource(
                                                                master_p,
                                                                self._dockings,
                                                                self._dockingpools,
                                                                "Workstations",
                                                                "swissdock",
                                                                "sib-pc61.unil.ch",
                                                                "22",                                  
                                                                "/etc/swissdock/id_dsa",
                                                                "/export/home/swissdock/tmp",
                                                                "submission/launch.workstations.unil.ch",
                                                                self._localCacheDirectory
                                                                ))
            self._computingResource[2].setAllowPooledJobs(False)
#        self._computingResource.append(SingleHostComputingResource(
#                                                            master_p,
#                                                            runningDocking_p,
#                                                            "sib-pc61",
#                                                            "swissdock",
#                                                            "localhost",
#                                                            "2024",
#                                                            #"sib-pc61.unil.ch",
#                                                            #"22",
#                                                            "/etc/swissdock/id_dsa",
#                                                            "/home/swissdock/swissdock/tmp/",
#                                                            "submission/launch.sib-pc61.unil.ch",
#                                                            self._localCacheDirectory
#                                                            ))        
        self.shouldStop = False                
        
    def _addResource(self, currentResource):
        print "Storing New resource %s as %s" % (currentResource['type'], currentResource['res_name'])
        a = globals()[currentResource['type']](
                                               self._master,
                                                self._dockings,
                                                self._dockingPools,
                                                currentResource['res_name'],
                                                currentResource['user_name'],
                                                currentResource['host_name'],
                                                currentResource['ssh_port'],
                                                currentResource['ssh_key'],
                                                currentResource['tmp_dir'],
                                                currentResource['submission_script'],
                                                self._localCacheDirectory,
                                                len(self._computingResource)                                                
                                                )
        a.setAllowPooledJobs(currentResource['allow_pooled_jobs'] == "true") 
        self._computingResource.append(a)
        
        
    def _logMessage(self, msg):
        self._master._logMessage(msg)

    def _startDocking(self, dockingID):
        currentDocking = self._dockings.getDocking(dockingID)
        parameters = currentDocking.parameters
        directory = "%s/%s" % (self._master._TMPDIR, dockingID)
        currentJobID = os.path.basename(directory)
        msg = "%s started a docking preparation in %s" % (parameters['emailAddress'], directory)
        mailreport = msg
        self._logMessage(msg)
        targetPsf = currentDocking.getTargetPsf()
        targetCrd = currentDocking.getTargetCrd()
        ligandPdb = currentDocking.getLigandPdb()
        ligandRtf = currentDocking.getLigandRtf()
        ligandPar = currentDocking.getLigandPar()

        if len(ligandRtf) > 1 or  len(ligandPar) > 1:
            msg = "Merging multiple RTF/PAR files"
            self._logMessage(msg)
            charmm = CharmmWrapper()
            (mergedPar, mergedRtf) = charmm.mergeTopPar(ligandRtf, ligandPar)
        else:
            mergedPar = ligandPar[0]
            mergedRtf = ligandRtf[0] 
        
        files = dict ( { "target.psf": targetPsf, "target.crd": targetCrd, "ligand.pdb": ligandPdb, "ligand.rtf": mergedRtf, "ligand.par": mergedPar } )        
        for filename, content in files.items():
            if content is not None:
                f = open("%s/%s" %(directory, filename), "w")
                f.write(content)
                f.close()
                msg = "Docking preparation: file %s written" % filename
                self._logMessage(msg)
                mailreport = "%s\r\n%s" % (mailreport, msg)
            else:
                msg = "Docking preparation: file %s skipped (content is None)" % filename
                self._logMessage(msg)
                mailreport = "%s\r\n%s" % (mailreport, msg)
                pass
        
        # Load target and ligand in CHARMM and dump appropriate complex.crd and complex.psf
        msg = "Docking preparation: creating CHARMM complex"
        self._logMessage(msg)
        mailreport = "%s\r\n%s" % (mailreport, msg)
        try:         
            charmm = CharmmWrapper()   
            charmm.autoStart(cwd=directory)
            charmm.appendPdb("ligand.pdb", segid="LIG" )
            charmm.writePsf("complex.psf")
            charmm.writeCrd("complex.crd")
            charmm.executeAndForget("ENERGY")
            charmm.stop()
            time.sleep(5)
            if charmm.process.returncode != 0:
                raise Exception("CHARMM exits with non zero status")            
            if ( len(filter ( lambda name: os.path.isfile("%s/%s"%(directory, name)), ["complex.psf", "complex.crd"])) != 2 ):
                raise Exception("Complex files not generated")
        except Exception:
            msg = "Docking preparation: complex generation failed in %s: %s" % (directory, traceback.print_exc())
            self._logMessage(msg)
            mailreport = "%s\r\n%s" % (mailreport, msg)
            self._master.sendReport("Docking %s : complex generation failed in %s"%(currentJobID,directory), mailreport)
            return False
            
        # clean up files
        extraFiles = filter( lambda name: str(name).startswith("target"), os.listdir(directory) )
        extraFiles.extend( filter( lambda name: str(name).startswith("ligand.pdb"), os.listdir(directory) ) )
        extraFiles.extend( filter( lambda name: str(name).startswith("charmm"), os.listdir(directory) ) )
        for file in extraFiles:
            msg = "Docking preparation: removing %s" % file
            self._logMessage(msg)
            mailreport = "%s\r\n%s" % (mailreport, msg)
            os.remove("%s/%s"%(directory, file))
        
        # Create param file
        msg = "Docking preparation: creating parameter file"
        self._logMessage(msg)
        mailreport = "%s\r\n%s" % (mailreport, msg)
        f = open ("%s/params" % directory, "w")
        f.write("JOBNAME: %s\n" % parameters['jobName'])
        if parameters['emailAddress'] is not None and parameters['dockingPoolID'] is None :
            f.write("EMAIL: %s\n" % parameters['emailAddress'])
        
        if parameters['xmin'] is not None:
            f.write("XMIN: %s\n" % parameters['xmin'])
        if parameters['xmax'] is not None:
            f.write("XMAX: %s\n" % parameters['xmax'])
        if parameters['ymin'] is not None:
            f.write("YMIN: %s\n" % parameters['ymin'])
        if parameters['ymax'] is not None:
            f.write("YMAX: %s\n" % parameters['ymax'])
        if parameters['zmin'] is not None:
            f.write("ZMIN: %s\n" % parameters['zmin'])
        if parameters['zmax'] is not None:
            f.write("ZMAX: %s\n" % parameters['zmax'])
        
        if parameters['passiveFlexibilityDistance'] is not None:
            f.write("PASSIVEFLEXIBILITYDISTANCE: %s\n" % parameters['passiveFlexibilityDistance'])
        
        if parameters['wantedConfs'] is not None:
            f.write("WANTEDCONFS: %s\n" % parameters['wantedConfs'])
        if parameters['nbFactsEval'] is not None:
            f.write("NBFACTSEVAL: %s\n" % parameters['nbFactsEval'])
        if parameters['nbSeeds'] is not None:
            f.write("NBSEEDS: %s\n" % parameters['nbSeeds'])
        
        if parameters['sdSteps'] is not None:
            f.write("SDSTEPS: %s\n" % parameters['sdSteps'])
        if parameters['abnrSteps'] is not None:
            f.write("ABNRSTEPS: %s\n" % parameters['abnrSteps'])
        
        if parameters['clusteringRadius'] is not None:
            f.write("CLUSTERINGRADIUS: %s\n" % parameters['clusteringRadius']) # Not implemented in eadock_simple.lsf
        if parameters['maxClusterSize'] is not None:
            f.write("MAXCLUSTERSIZE: %s\n" % parameters['maxClusterSize']) # Not implemented in eadock_simple.lsf
        if parameters['ignorePocketBias'] == 1:
            f.write("IGNOREPOCKETBIAS: true\n") # Not implemented in eadock_simple.lsf
        if parameters['keepLigandInPlace'] == 1:
            f.write("USETRANSLATIONS: false\n") # Not implemented in eadock_simple.lsf

        f.close()

        if parameters['dockingPoolID'] is not None:
            f = open ("%s/dockingpoolid" % directory, "w")
            f.write(parameters['dockingPoolID'])
            f.close()
            
        mailreport = "%s\r\n%s" % (mailreport, msg)
        return True
        
    def checkComputingResources(self):
        for i in range (0, len(self._computingResource)):
            self._computingResource[i].checkResource()
        
        
    def run(self):
        trigger = self._computingResourcesPollInterval // self._dockingQueuePollInterval
        count = 0
        while (not self.shouldStop) :
            while (len(self._dockings.getQueuedDockingIDs()) == 0) :
                time.sleep(self._dockingQueuePollInterval)
                count+=1
                #print "Waiting %s s" % self._dockingQueuePollInterval 
                if count % trigger == 0: 
                    #print "Checking resources"
                    self.checkComputingResources()
                    count = 0
            try:
                queuedDockingIDs = self._dockings.getQueuedDockingIDs()
                for identifier, docking in queuedDockingIDs.items():
                    chosenResource = -1
                    for i in range (0, len(self._computingResource)):
                        if docking.parameters['dockingPoolID'] is not None and not self._computingResource[i].allowPooledJobs():
                            continue
                        if self._computingResource[i].isReady :
                            chosenResource = i
                            break
                    if chosenResource == -1:
                        msg = "No available computing resource found for docking %s, canceling job !" % docking.name
                        self._master.sendReport(msg, msg)                        
                        self._logMessage(msg)                        
                        docking.status = Docking.TERMINATED
                        docking.localpath = "%s/%s" % (self._master._TMPDIR, identifier)
                        continue
                    try:
                        output = self._startDocking(identifier)
                        if output:
                            self._computingResource[chosenResource].submit(identifier)                                
                            docking.resource = chosenResource
                        else:
                            docking.status = Docking.TERMINATED
                            raise Exception("Complex preparation failed")
                    except Exception, err:
                        msg = "Dispatching of docking %s failed in %s: %s" % (identifier,identifier,str(err))
                        self._master.sendReport(msg, msg)
                        self._logMessage(msg)
                        traceback.print_exc()                                
                time.sleep(1)
                self.checkComputingResources()
            except Exception, err:
                msg = "Error while dispatching queued jobs: %s" % (str(err))
                self._master.sendReport(msg ,msg)
                self._logMessage(msg)
                traceback.print_exc()

