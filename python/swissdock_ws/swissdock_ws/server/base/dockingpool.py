#!/usr/bin/python

'''
Created on Oct 28, 2011

@author: aurelien
'''

class DockingPool():
    status = None
    identifier = None
    localpath = None
    dockings = None
    WAITING = 0
    RUNNING = 1
    TERMINATED = 2

    def __init__(self):
        self.dockings = list()