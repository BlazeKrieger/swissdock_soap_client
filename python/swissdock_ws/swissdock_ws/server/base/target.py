#!/usr/bin/python

'''
Created on Oct 28, 2011

@author: aurelien
'''

class Target():
    status = None
    identifier = None
    query = None
    files = None
    msg = None
    PREPARING = 0
    PREPARED = 1
    CRASHED = 2

