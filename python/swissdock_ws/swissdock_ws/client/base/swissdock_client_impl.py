#!/usr/bin/python

'''
Created on Jan 27, 2010

@author: aurelien
'''

import swissdock_ws.SOAPpy
import time
from optparse import OptionParser
import zlib

class SwissdockClient:
    
    _PollTime = 30

    def _readFile(self, filename):
        try:
            f = open (filename)
            toReturn = f.read()
            f.close
        except Exception, err:
            print 'ERROR: %s\n' % str(err)
        return toReturn

    def _writeFile(self, filename, content):
        try:
            f = open (filename, "w")
            f.write(content)
            f.close
        except Exception, err:
            print 'ERROR: %s\n' % str(err)
            return False
        return True
    
    def _logMessage(self, message):
        if not self.options.quiet :
            print message
        
    def printStatus(self):
        if self.getStatus():
            print "Job %s terminated" % self.options.jobid
        else:
            print "Job %s not terminated" % self.options.jobid

    def getStatus(self):
        return self.isDockingTerminated(self.options.jobid)

    def retrievePrediction(self):
        try:
            if self.options.retrieveallfiles is True:
                self._logMessage("Retrieving all files generated during the execution of job %s in output.zip"% self.options.jobid)
                outputFiles = self.getPredictedDockingAllFiles(self.options.jobid)
                self._writeFile("output.zip", outputFiles)
            else:
                self._logMessage("Retrieving files for job %s "% self.options.jobid)
                outputFiles = self.getPredictedDocking(self.options.jobid)
                self._writeFile("target.pdb", outputFiles[0])
                self._writeFile("clusters.dock4", outputFiles[1])
        except Exception, err:
            print "Cannot write files: %s" % str(err)
    
    def parseArguments(self):
        try:
            parser = OptionParser()
            # general options
            parser.add_option("-q", "--quiet", dest="quiet", action="store_true", default=False, help="quiet mode")    
            parser.add_option("-i", "--interactive", dest="interactive", action="store_true", default=False, help="wait for the prediction to complete", metavar="INTERACTIVE")
            parser.add_option("-o", "--setuponly", dest="setuponly", action="store_true", default=False, help="only performs the setup of the specificed target and/or ligand, and exits", metavar="SETUPONLY")
            
            # system definition            
            parser.add_option("-t", "--target", dest="target", help="PDB code or PDB file name for your target structure, eg. 2BCJ", metavar="TARGET")
            parser.add_option("-T", "--charmmtarget", dest="charmmtarget", help="coma-separated list of PSF,CRD files for your target structure", metavar="CHARMMTARGET")
            parser.add_option("-l", "--ligand", dest="ligand", help="ZINC code or MOL2 file name for your ligand structure, eg. 8215481", metavar="LIGAND")
            parser.add_option("-L", "--charmmligand", dest="charmmligand", help="coma-separated list of PDB,RTF,PAR (if any) files for your target structure", metavar="CHARMMLIGAND")

            # docking options
            # TODO imeplemnt default values for xmin, xmax, ymin, ymax, zmin, xmax : check value in eadock_simple.lsf ?
            defaultWantedConfs = 5000
            defaultNbFactsEval = 500
            defaultNbSeeds = 250
            defaultsdsteps = 50
            defaultabnrteps = 100
            defaultClusteringRadius = 2
            defaultMaxClusterSize = 8
            defaultPassiveFlexibilitDistance = 0
            defaultignorepocketbias = False
            defaultkeepligandinplace = False
            # defaultServer = "swissdock.vital-it.ch/soap/wsdl"
            defaultServer = "http://www.swissdock.ch/soap/wsdl"
            parser.add_option("-x", "--xmin", dest="xmin", help="X min", metavar="XMIN", default=0)
            parser.add_option("-X", "--xmax", dest="xmax", help="X max", metavar="XMAX", default=0)
            parser.add_option("-y", "--ymin", dest="ymin", help="Y min", metavar="YMIN", default=0)
            parser.add_option("-Y", "--ymax", dest="ymax", help="Y max", metavar="YMAX", default=0)
            parser.add_option("-z", "--zmin", dest="zmin", help="Z min", metavar="ZMIN", default=0)
            parser.add_option("-Z", "--zmax", dest="zmax", help="Z max", metavar="ZMAX", default=0)
            parser.add_option("-w", "--wantedconfs", dest="wantedconfs", default=defaultWantedConfs, help="Number of conformation to sample with DSS, default %s" % defaultWantedConfs, metavar="WANTEDCONFS")
            parser.add_option("-f", "--nbfactseval", dest="nbfactseval", default=defaultNbFactsEval, help="Number of conformation to evaluate with FACTS, default %s" % defaultNbFactsEval, metavar="NBFACTSEVAL")
            parser.add_option("-N", "--nbseeds", dest="nbseeds", default=defaultNbSeeds, help="Number of conformation to be returned to you, default %s" % defaultNbSeeds, metavar="NBSEEDS")
            parser.add_option("-m", "--sdsteps", dest="sdsteps", default=defaultsdsteps, help="Number of SD minimization steps, default %s" % defaultsdsteps, metavar="sdsteps")
            parser.add_option("-M", "--abnrsteps", dest="abnrsteps", default=defaultabnrteps, help="Number of ABNR minimization steps, default %s" %defaultabnrteps, metavar="abnrsteps")
            parser.add_option("-R", "--clusteringradius", dest="clusteringradius",default=defaultClusteringRadius, help="Clustering radius in A, default %s" % defaultClusteringRadius, metavar="clusteringradius")
            parser.add_option("-S", "--maxclustersize", dest="maxclustersize", default=defaultMaxClusterSize, help="maximum size of a cluster, default %s" %defaultMaxClusterSize, metavar="maxclustersize")
            parser.add_option("-F", "--passiveFlexibilityDistance", dest="passiveFlexibilityDistance", default=defaultPassiveFlexibilitDistance, help="passive flexibility distance threshold, default %s" % defaultPassiveFlexibilitDistance, metavar="passiveFlexibilityDistance")            
            parser.add_option("-I", "--ignorepocketbias", dest="ignorepocketbias", action="store_true", default=defaultignorepocketbias, help="Ignore pocket bias - NOT AVAILABLE YET, default %s"%defaultignorepocketbias, metavar="IGNOREPOCKETBIAS")
            parser.add_option("-P", "--keepligandinplace", dest="keepligandinplace", action="store_true", default=defaultkeepligandinplace, help="Do not translate the ligand - NOT AVAILABLE YET, default %s"%defaultkeepligandinplace, metavar="KEEPLIGANDINPLACE")
            

            # authentification options
            parser.add_option("-n", "--name", dest="name", help="sets job name, mandatory", metavar="NAME")
            parser.add_option("-e", "--email", dest="email", help="email address, mandatory", metavar="EMAIL")
            parser.add_option("-p", "--password", dest="password", default="", help="password, not required yet", metavar="PASSWORD")
            parser.add_option("-H", "--host", dest="server", default=defaultServer, help="server to connect to (IP or name) and destination port (if any), default %s"%defaultServer, metavar="SERVER")

            # alternative action
            parser.add_option("-j", "--jobid", dest="jobid", help="Job ID", metavar="JOBID")
            parser.add_option("-s", "--status", dest="status", action="store_true", default=False, help="print the status of a job", metavar="JOBID")
            parser.add_option("-r", "--retrieve", dest="retrieve", action="store_true", default=False, help="retrieve the prediction for the job locally in target.pdb and clusters.dock4", metavar="JOBID")
            parser.add_option("-a", "--retrieve-all-files", dest="retrieveallfiles", action="store_true", default=False, help="retrieve a ZIP file containing all files generated during the docking assay", metavar="RETRIEVEALLFILES")

            (self.options, self.args) = parser.parse_args()
        except Exception, err:
            print 'ERROR: %s\n' % str(err)
        
    def _prepareTarget(self):
        # PDB or PDB accession number is provided
        try:
            f = open(self.options.target)
            targetString = f.read()
            f.close()
            self._logMessage("Reading target from %s" % self.options.target)
            print("Reading target from %s" % self.options.target)
        except:
            targetString = self.options.target
        self._logMessage("Reading target %s from database" % self.options.target)
        targetPreparationJobID = self.prepareTarget(targetString)
        self._logMessage("Target preparation ID: %s" % targetPreparationJobID)
        while True:
            outcome = self.isTargetPrepared(targetPreparationJobID) 
            if outcome is None:
                self._logMessage("Target preparation: No such target %s " % targetPreparationJobID)
                exit(1)
            elif outcome is False or outcome == "false" or outcome == 0:
                time.sleep(self._PollTime)
            else:
                break                
        targetFiles = self.getPreparedTarget(targetPreparationJobID)
        if targetFiles is None:
            self._logMessage("Target preparation unknown error")
            exit(1)
        if len(targetFiles) != 2:
            self._logMessage("Target preparation error: %s " % targetFiles)
            exit(1)
        return targetFiles

    def _prepareLigand(self):
        # MOL2 or ZINC accession number is provided
        try:
            f = open(self.options.ligand)
            ligandString = f.read()
            f.close()
            self._logMessage("Reading ligand from %s" % self.options.ligand)
            print("Reading ligand from %s" % self.options.ligand)
        except:
            ligandString = self.options.ligand
            self._logMessage("Reading ligand %s from database" % self.options.ligand)
        ligandPreparationJobID = self.prepareLigand(ligandString)
        self._logMessage("Ligand preparation ID: %s" % ligandPreparationJobID)
        
        while True:
            outcome = self.isLigandPrepared(ligandPreparationJobID)
            if outcome is None:
                self._logMessage("Ligand preparation: No such ligand %s " % ligandPreparationJobID)
                exit(1)
            elif outcome is False or outcome == "false" or outcome == 0:
                time.sleep(self._PollTime)
            else:
                break
        ligandFiles = self.getPreparedLigand(ligandPreparationJobID)
        if ligandFiles is None:
            self._logMessage("Ligand preparation unknown error")
            exit(1)
        if len(ligandFiles) != 3:
            self._logMessage("Ligand preparation error: %s " % ligandFiles)
            exit(1)
        return ligandFiles

        
    def run(self):
        
        print('Running...')
        
        self.parseArguments()
        self.initServer(self.options.server)
    
        if self.options.setuponly is True:
            if self.options.target is None and self.options.ligand is None:
                print "Please provide at least a ligand and/or a target, exiting..."
                exit(0)
            if self.options.target is not None:
                print "Preparing target..."
                targetFiles = self._prepareTarget()
                # TODO Do not assume that files are ordered, but check their extensions                
                self._writeFile("target.psf", targetFiles[0])
                self._writeFile("target.crd", targetFiles[1])
                # write target files ?
            if self.options.ligand is not None:
                print "Preparing ligand..."
                ligandFiles = self._prepareLigand()
                # TODO Do not assume that files are ordered, but check their extensions
                self._writeFile("lig.pdb", ligandFiles[0])
                self._writeFile("lig.rtf", ligandFiles[1])
                self._writeFile("lig.par", ligandFiles[2])
            exit(0)
    
        if self.options.status is True:
            if self.options.jobid is not None:
                self.printStatus()
            else:
                print "No job identifier provided, exiting..."
            exit(0)
        
        if self.options.retrieve is True:
            if self.options.jobid is not None:
                self.retrievePrediction()
            else:
                print "No job identifier provided, exiting..."
            exit(0)

        if self.options.name is None:
            print "No job name provided, exiting..."
            exit(0)
            
        if self.options.email is None:
            print "No email address provided, exiting..."
            exit(0)

        #
        # prepare target files
        #
        if self.options.charmmtarget is not None:
            # CHARMM files are provided
            charmmfiles = self.options.charmmtarget.split(",")
            if len(charmmfiles) == 2:
                # TODO Do not assume that files are ordered, but check their extensions
                targetFiles = [ self._readFile(charmmfiles[0]), self._readFile(charmmfiles[1]) ]
                self._logMessage("Reading target from PSF:%s and CRD:%s" % (charmmfiles[0], charmmfiles[1]) )
            elif len(charmmfiles) == 4:
                # TODO Do not assume that files are ordered, but check their extensions
                targetFiles = [ self._readFile(charmmfiles[0]), self._readFile(charmmfiles[1]), self._readFile(charmmfiles[2]), self._readFile(charmmfiles[3]) ]
                self._logMessage("Reading target from PSF:%s, CRD:%s, RTF:%s and PAR:%s" % (charmmfiles[0], charmmfiles[1], charmmfiles[2], charmmfiles[3]) )

        else:           
            targetFiles = self._prepareTarget()        
        
        #
        # prepare ligand files
        #
        if self.options.charmmligand is not None:
            # CHARMM files are provided
            charmmfiles = self.options.charmmligand.split(",")
            # TODO Do not assume that files are ordered, but check their extensions
            # Compress and encode in base64
            if len(charmmfiles) == 1:
                ligandFiles = [ self._readFile(charmmfiles[0]), None, None ]
                self._logMessage("Reading ligand from PDB:%s" % (charmmfiles[0]) )
            elif len(charmmfiles) == 3:
                ligandFiles = [ self._readFile(charmmfiles[0]), self._readFile(charmmfiles[1]), self._readFile(charmmfiles[2]) ]
                self._logMessage("Reading ligand from PDB:%s , RTF:%s and PAR:%s" % (charmmfiles[0], charmmfiles[1], charmmfiles[2]) )
            else:
                print "Please provide a PDB, a PAR, and a RTF for your ligand";
                exit(1)
        else:
            ligandFiles = self._prepareLigand()


        #targetFiles = map(lambda x: zlib.compress(x).encode("base64"), targetFiles)
        #ligandFiles = map(lambda x: zlib.compress(x).encode("base64"), ligandFiles)
        
        dockingPoolID = None
        # Check if none is added ?
        rtfList = list()
        parList = list()

            
        if len(targetFiles) == 4:
            rtfList.append(targetFiles[2])
            parList.append(targetFiles[3])
            
        if len(ligandFiles) == 3:
            rtfList.append(ligandFiles[1])
            parList.append(ligandFiles[2])
                    
        self.options.jobid = self.startDocking(
                                           targetFiles[0],
                                           targetFiles[1],
                                           ligandFiles[0],
                                           rtfList,
                                           parList,
                                           self.options.name,
                                           self.options.email,
                                           self.options.password,
                                           self.options.xmin, self.options.xmax,
                                           self.options.ymin, self.options.ymax,
                                           self.options.zmin, self.options.zmax, 
                                           self.options.wantedconfs,
                                           self.options.nbfactseval,
                                           self.options.nbseeds,
                                           self.options.sdsteps, self.options.abnrsteps,
                                           self.options.clusteringradius, self.options.maxclustersize, self.options.passiveFlexibilityDistance,
                                           self.options.ignorepocketbias, self.options.keepligandinplace,
                                           dockingPoolID
                                           )


        # TEST Block
#        dockingPoolID = self.getNewDockingPool()
#        oldName = self.options.name 
#        for i in range(1):
#            self.options.name = "%s.%s" % (oldName, i)
#            self.options.jobid = self.startDocking(
#                                               targetFiles[0],
#                                               targetFiles[1],
#                                               ligandFiles[0],
#                                               ligandFiles[1],
#                                               ligandFiles[2],
#                                               self.options.name,
#                                               self.options.email,
#                                               self.options.password,
#                                               self.options.xmin, self.options.xmax,
#                                               self.options.ymin, self.options.ymax,
#                                               self.options.zmin, self.options.zmax, 
#                                               self.options.wantedconfs,
#                                               self.options.nbfactseval,
#                                               self.options.nbseeds,
#                                               self.options.sdsteps, self.options.abnrsteps,
#                                               self.options.clusteringradius, self.options.maxclustersize, self.options.passiveFlexibilityDistance,
#                                               self.options.ignorepocketbias, self.options.keepligandinplace,
#                                               dockingPoolID
#                                               )
#        self.options.name = oldName                 
#        while not self.isDockingPoolTerminated(dockingPoolID):
#            time.sleep(self._PollTime)
#            self._logMessage("Interactive mode: waiting %d second more" % self._PollTime)
                
        # END TEST Block
        
        
        if self.options.jobid == "None":
            print "Your docking was not submitted. Please check that %s is accessible." % self.options.server
            exit(1)

        self._logMessage("Job %s submitted" % self.options.jobid)
        if self.options.interactive is False:
            exit(0)

        while not self.isDockingTerminated(self.options.jobid):
            time.sleep(self._PollTime)
            self._logMessage("Interactive mode: waiting %d second more" % self._PollTime)
    
        self.retrievePrediction()
        self.forget(self.options.jobid)
        exit(0)       

if __name__ == "__main__":
    sdc = SwissdockClient()
    sdc.run()

