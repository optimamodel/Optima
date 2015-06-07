# -*- coding: utf-8 -*-
"""
Created on Fri Jun 05 23:27:38 2015

@author: David Kedziora
"""

class Sim:
    def __init__(self, simname):
        self.simname = simname
        self.processed = False      # This tag monitors if the simulation has been run.
        
        self.parsdata = None        # This used to be D['P'].
        self.parsmodel = None       # This used to be D['M'].
        self.parsfitted = None      # This used to be D['F'].
        
        self.results = None         # This used to be D['R'].
        self.structure = None       # This used to be D['S'].
        
        self.plotdata = None        # This used to be D['plot']['E']. Be aware that it is not D['plot']!        
        self.plotdataopt = []       # This used to be D['plot']['optim']. Be aware that it is not D['plot']!
        
    def setsimname(self, simname):
        self.simname = simname
        
    def getsimname(self):
        return self.simname
        
    def isprocessed(self):
        return self.processed
    
    # Initialises P, M and F matrices belonging to the Sim object, but does not run simulation yet.
    # Very dangerous, as stability relies on the trust that no data passed in is being changed behind the scenes...
    def initialise(self, regiondata, regionmetadata, regionoptions):
        
        from makedatapars import makedatapars
        
        # Explicit construction of tempD, so that one day we know how to recode makedatapars.
        tempD = dict()
        tempD['data'] = regiondata
        tempD['G'] = regionmetadata
        
        tempD = makedatapars(tempD)
        self.parsdata = tempD['P']
        
        from makemodelpars import makemodelpars
        
        self.parsmodel = makemodelpars(self.parsdata, regionoptions)
        
        from updatedata import makefittedpars
        
        # Explicit construction of tempD, so that one day we know how to recode makefittedpars.
        tempD = dict()
        tempD['opt'] = regionoptions
        tempD['G'] = regionmetadata
        tempD['M'] = self.parsmodel
        
        tempD = makefittedpars(tempD)
        self.parsfitted = tempD['F']
    
    # Runs model given all the initialised parameters.
    def run(self, regiondata, regionmetadata, regionoptions, regionprograms):
        
        from model import model

        allsims = []
        for s in range(len(self.parsfitted)):   # Parallelise eventually.
            S = model(regionmetadata, self.parsmodel, self.parsfitted[s], regionoptions)
            allsims.append(S)
        self.structure = allsims[0]     # Save one full sim structure for troubleshooting and... funsies?
    
        # Calculate results.
        from makeresults import makeresults
        
        # Explicit construction of tempD, so that one day we know how to recode makeresults.
        tempD = dict()
        tempD['G'] = regionmetadata
        tempD['P'] = self.parsdata
        tempD['S'] = self.structure
        
        # Input that only the financialanalysis subfunction in makeresults wants.
        # It would be a good idea to somehow separate the two...
        tempD['data'] = regiondata
        tempD['opt'] = regionoptions
        tempD['programs'] = regionprograms
        
        self.results = makeresults(tempD, allsims, regionoptions['quantiles'])
    
        # Gather plot data.
        from gatherplotdata import gatheruncerdata
        
        tempD = dict()
        tempD['data'] = regiondata
        tempD['G'] = regionmetadata
        
        self.plotdata = gatheruncerdata(tempD, self.results)
        
        self.processed = True
    
    # Currently just optimises simulation according to defaults.
    def optimise(self, regiondata, regionmetadata, regionoptions, regionprograms):
        
        from optimize import optimize
        
        tempD = dict()
        tempD['data'] = regiondata
        tempD['opt'] = regionoptions
        tempD['programs'] = regionprograms
        tempD['G'] = regionmetadata
        tempD['P'] = self.parsdata
        tempD['M'] = self.parsmodel
        tempD['F'] = self.parsfitted
        tempD['R'] = self.results
        tempD['plot'] = dict()
        tempD['plot']['optim'] = self.plotdataopt
        
        tempD['S'] = self.structure     # Error rising. Where does S come from? Do I need to run simulation first?
        optimize(tempD, maxiters = 1)   # Temporary restriction on iterations. Not meant to be hardcoded!
        
        
    def plotresults(self):
        
        from viewresults import viewuncerresults
        
        viewuncerresults(self.plotdata, show_wait = True)