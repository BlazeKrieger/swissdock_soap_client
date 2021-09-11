#!/usr/bin/python

'''
Created on Oct 28, 2011

@author: aurelien
'''
from threading import Thread
import time
import urllib
import tempfile
import hashlib
import os
import shlex
from subprocess import PIPE, Popen
import traceback
from swissdock_ws.server.base.ligand import Ligand
import re

class PrepareLigandThread(Thread):
    
    def __init__(self, master_p, ligands_p):
        Thread.__init__(self, name="prepareLigandThread")
        self._master = master_p
        self._ligands = ligands_p
        self.shouldStop = False
        self._POLLTIME = 1
        
    def _logMessage(self, msg):
        self._master._logMessage(msg)
    
    def run(self):    
        while (not self.shouldStop) :
            while (len(self._ligands.getPreparingLigandIDs()) == 0) :
                time.sleep(self._POLLTIME)
                pass
            preparingLigandList = self._ligands.getPreparingLigandIDs()
            self._logMessage("Found %s in the ligand preparation queue, processing" % len(preparingLigandList))
            for identifier in preparingLigandList:
                ligand = self._ligands.getLigand(identifier)
                self._logMessage("Ligand %s preparation: started" % identifier)
                try:
                    if ligand.query.count("\n") < 2:
                        self._logMessage("Ligand %s preparation: reading %s from ZINC" % (identifier, ligand.query))
                        url = "http://zinc.docking.org/substance/%s" % ligand.query
                        f = urllib.urlopen(url)
                        t  = f.read()
                        m = re.search("a href=\"(.+)\" title=\"Download MOL2 File\"",t)
                        if m:
                            url = m.group(1)
                            f = urllib.urlopen(url)
                            ligand.query = f.read()
                        else:
                            raise Exception("ZINC AC %s not found" % ligand.query)
                        # TODO Fix MOl2 retrieval from ZINC AC
                        
                    else:
                        self._logMessage("Ligand %s preparation: reading from data structure" % identifier)
                    directory = "%s/ligand.%s" % (self._master._TMPDIR, hashlib.sha256(ligand.query).hexdigest())
                    if not os.path.exists(directory):
                        os.mkdir(directory)
                        tmpFile = tempfile.mkstemp(suffix=".mol2", dir=directory)
                        self._logMessage("Ligand %s preparation: dumping to file %s" % (identifier, tmpFile[1]))
                        f = os.fdopen(tmpFile[0], "w")
                        f.write(ligand.query)
                        f.close()
                        self._logMessage("Ligand %s preparation: converting to CHARMM format" % identifier)
                        cmd = "%s %s" % (self._master._MOL2MMFF, os.path.basename(tmpFile[1]))                        
                        args = shlex.split(cmd)
                        process = Popen(args, stdout=PIPE, stderr=PIPE, cwd=directory)
                        output = process.communicate()                        
                        if output[0] != "":
                            self._logMessage("Ligand %s preparation: conversion stdout: %s" % (identifier, output[0]))
                        if output[1] != "":
                            self._logMessage("Ligand %s preparation: conversion stderr: %s" % (identifier, output[1]))
                        process.stderr.close()
                        process.stdout.close()
                    else:
                        self._logMessage("Reading %s from cache" % (identifier))
                    filenames = dict( { "RTF":"lig.rtf", "PAR":"lig.par", "PDB":"compound.pdb" } )
                    ligandFiles = dict()                
                    for type, filename in filenames.items(): 
                        f = open("%s/%s" % (directory, filename), "r")
                        ligandFiles[type] = f.read()
                        f.close()   
                    self._logMessage("Ligand %s preparation: success" % identifier)
                    ligand.status = Ligand.PREPARED
                    ligand.files = [ ligandFiles["PDB"], ligandFiles["RTF"], ligandFiles["PAR"] ]
                except Exception:
                    msg = "Setup of ligand %s failed in %s" % (identifier, directory);
                    self._master.sendReport(msg, msg)
                    self._logMessage(msg)
                    traceback.print_exc()                    
                    ligand.status = Ligand.CRASHED
                    ligand.msg = [ msg ]

