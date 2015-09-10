# -*- coding: utf-8 -*-
"""
Created on Fri May 29 23:16:12 2015

@author: David Kedziora
"""

import defaults
from simbox import SimBox
from simboxopt import SimBoxOpt
from simboxcal import SimBoxCal
import sim
import setoptions
import uuid
import program
from numpy import array, isnan, zeros, shape, mean
from liboptima.utils import sanitize, perturb,printv
import liboptima.dataio_binary as dataio_binary
from programset import ProgramSet
from scipy.interpolate import PchipInterpolator as pchip
import cPickle

class Project(object):
    def __init__(self,name,populations=None,programs=None,datastart=None,dataend=None):
        # Usage
        # r = Project(name,populations,programs,datastart,dataend) (see defaults.py haiti) 
        # r = Project(projectdict) -> projectdict = r.fromdict()

        if isinstance(name,dict):
            # variable 'name' is actually a projectdict
            self.fromdict(name)
        else:
            self.D = dict()                 # Data structure for saving everything. Will hopefully be broken down eventually.
                  
            self.metadata = defaults.metadata  # Loosely analogous to D['G']. Start with default HIV metadata
            self.metadata['datastart'] = datastart
            self.metadata['dataend'] = dataend
            self.metadata['populations'] = populations
            self.metadata['programs'] = programs
            self.metadata['name'] = name

            self.data = None

            self.options = setoptions.setoptions() # Populate default options here
            
            # Budget Objective Curve data, used for GPA. (Assuming initial budget spending is fixed.)
            self.BOCx = []        # Array of budget allocation totals.
            self.BOCy = []        # Array of corresponding optimum objective values.
            
            self.programsets = []
            self.calibrations = []        # Remember. Current BOC data assumes loaded data is calibrated by default.
            
            self.simboxlist = []            # Container for simbox objects (e.g. optimisations, grouped scenarios, etc.)
            
            self.uuid = None
            self.genuuid()  # Store UUID as a string - we just want a (practically) unique tag, no advanced functionality
            self.current_version = 2 # This is stored in the projectdict

    @classmethod
    def load(Project,filename,name=None):
        # Use this function to load a project saved with project.save
        r = Project(name,None,None,None,None)
        projectdict = dataio_binary.load(filename)
        r.uuid = projectdict['uuid'] # Loading a project restores the original UUID
        r.fromdict(projectdict)
        return r

    def save(self,filename):
        dataio_binary.save(self.todict(),filename)
                    
    @classmethod
    def load_json(Project,filename,name=None):
        # Create a new project by loading a JSON file
        # If a name is not specified, the one contained in the JSON file is used
        # Note that this function can be used with an old-type or new-type JSON file
        # A new-type JSON file will read a Project object including the UUID
        # While an old-type JSON file corresponds to 'D' and the project will get a new UUID
        r = Project(name,None,None,None,None)

        import dataio
        projectdict = dataio.loaddata(filename)
        if 'uuid' in projectdict.keys(): # This is a new-type JSON file
            print "This is a new-type JSON file."
            r.fromdict(projectdict)
        else:
            r.fromdict_legacy(projectdict)
        return r

    def save_json(self,filename):
        import dataio
        dataio.savedata(filename,self.todict())

    def __getstate__(self):
        # Note that this pickling method should only be implemented for classes
        # that can be saved directly i.e. portfolios and projects
        # simboxes and sims need more care so that the project references are
        # handled correctly
        return self.todict()

    def __setstate__(self, state):
        self.fromdict(state)

    def upgrade_version(self,projectdict):
        # Upgrade the saved project dictionary prior to running fromdict()
        # Note that projectdict is a reference, so code here changes the projectdict externally!
        if projectdict['version'] <= 1: 
            # Version 1 projects did not have program sets - they can be created from the saved metadata
            # Note that fromdict() expects programsets to be serialized as a string
            pset = ProgramSet.import_legacy('Default',projectdict['metadata']['programs'])
            projectdict['programsets'] = [pset.todict()]

        # The statement below for calibrations handles loading earlier versions of the new-type JSON files
        # which don't have calibrations already defined. It is suggested in future that these projects should
        # be loaded, a new calibration created from D, and then saved again, so that this statement can be removed
        import numpy
        if isinstance(projectdict['calibrations'], float) and numpy.isnan(projectdict['calibrations']):
            projectdict['calibrations'] = [{'uuid':None}]

    def fromdict(self,projectdict):
        # Assign variables from a new-type JSON file created using Project.todict()
        self.upgrade_version(projectdict)

        self.uuid = projectdict['uuid'] # Loading a project restores the original UUID
        self.metadata = projectdict['metadata']
        self.data = projectdict['data']
        self.options = projectdict['options'] # Populate default options here
        self.programsets = [ProgramSet.fromdict(x) for x in projectdict['programsets']] # sets of Programs i.e. an array of sets of CCOCs
        self.calibrations = projectdict['calibrations']
        self.uuid = projectdict['uuid']
        self.D = projectdict['D']
        
        self.simboxlist = [SimBox.fromdict(x,self) for x in projectdict['simboxlist']]

        # BOC loading.
        self.BOCx = projectdict['BOC_budgets']
        self.BOCy = projectdict['BOC_objectives']
            
    def todict(self):
        # Return a dictionary representation of the object for use with Project.fromdict()
        projectdict = {}
        projectdict['version'] = self.current_version # Could do something later by checking the version number

        projectdict['metadata'] = self.metadata 
        projectdict['data'] = self.data 
        projectdict['simboxlist'] = [sbox.todict() for sbox in self.simboxlist]
        projectdict['options'] = self.options # Populate default options here = self.options 
        projectdict['programsets'] = [pset.todict() for pset in self.programsets] # Serialize the programset
        projectdict['calibrations'] = self.calibrations # Calibrations are stored as dictionaries
        projectdict['uuid'] = self.uuid 
        projectdict['D'] = self.D

        # BOC saving.
        projectdict['BOC_budgets'] = self.BOCx
        projectdict['BOC_objectives'] = self.BOCy    

        return projectdict

    def fromdict_legacy(self, tempD):
        # Load an old-type D dictionary into the project
        self.setD(tempD)                # It would be great to get rid of setD one day. But only when data is fully decomposed.
        
        current_name = self.metadata['name']
        self.metadata = tempD['G'] # Copy everything from G by default
        self.metadata['programs'] = tempD['programs']
        self.metadata['populations'] = self.metadata['inputpopulations']
        if current_name is not None: # current_name is none if this function is being called from Project.load()
            self.metadata['name'] = current_name
        else:
            self.metadata['name'] = self.metadata['projectname']

        self.data = tempD['data']
        self.data['current_budget'] = tempD['data']['costcov']['cost']

        self.options = tempD['opt']

        # Legacy programs can be imported from the project metadata
        self.programsets = [ProgramSet.import_legacy('Default',self.metadata['programs'])]

        # Make the calibration - legacy files have one calibration
        # Using pop will remove them from the project so that downstream calls
        # will raise errors if they are not updated to use the new calibration
        c = {}
        c['uuid'] = str(uuid.uuid4())
        c['name'] = 'Default'
        c['const'] = self.D['P'].pop('const')
        c['hivprev'] = self.D['P'].pop('hivprev')
        c['popsize'] = self.D['P'].pop('popsize')
        c['pships'] = self.D['P'].pop('pships')
        c['transit'] = self.D['P'].pop('transit')
        c['metaparameters'] = self.D.pop('F')
        self.calibrations.append(c)

        # Go through the scenarios and convert them
        if 'scens' in tempD.keys():
            sbox = self.createsimbox('Scenarios')
            for scenario in tempD['scens']: # Separate cases in the web list 
                newsim = sim.SimParameter(scenario['scenario']['name'],self)
                for par in scenario['scenario']['pars']:
                    newsim.create_override(par['names'],par['pops'],par['startyear'],par['endyear'],par['startval'],par['endval'])
                sbox.simlist.append(newsim)

    def fetch(self,target_uuid):
        # Fetch a simbox or a sim from within the project by looking up it's uuid
        for sbox in self.simboxlist:
            if sbox.uuid == target_uuid:
                return sbox
            else:
                for s in sbox.simlist:
                    if s.uuid == target_uuid:
                        return s
        for pset in self.programsets:
            if pset.uuid == target_uuid:
                return pset
        raise Exception('UUID not found')
        
    def createsimbox(self, simboxname, iscal = False, isopt = False, createdefault = True):
        if iscal and isopt:
            print('Error: Cannot create a simbox that is simultaneously for calibration and optimisation.')
            return None
        if iscal:
            self.simboxlist.append(SimBoxCal(simboxname,self))
        elif isopt:
            self.simboxlist.append(SimBoxOpt(simboxname,self))
        else:
            self.simboxlist.append(SimBox(simboxname,self))
        if createdefault:
            self.simboxlist[-1].createsim(simboxname + '-default')
        return self.simboxlist[-1]
        
    def createsiminsimbox(self, simname, simbox):
        new_sim = simbox.createsim(simname)
        return new_sim
    
    # Runs through every simulation in simbox (if not processed) and processes them.
    # May optimise too depending on SimBox type.
    def runsimbox(self, simbox):
        simbox.runallsims(forcerun = False)
        
    # Runs through every simulation in simbox (if processed) and plots them, either multiplot or individual style.
    def plotsimbox(self, simbox, multiplot = False):
        if multiplot:
            simbox.viewmultiresults()
            if isinstance(simbox, SimBoxOpt):
                simbox.viewoptimresults(plotasbar = False)
                simbox.viewoptimresults(plotasbar = True)
        else:
            simbox.plotallsims()
            
#%% GPA Methods
            
    # Method to generate a budget objective curve (BOC) for the Project.
    # Creates a temporary SimBoxOpt with a temporary SimBudget and calculates the BOC.
    # Ends by deleting the temporary objects and retaining BOC data.
    def developBOC(self, varfactors, forcecalc = False, extendresults = False):      
        if forcecalc or extendresults or not self.hasBOC():
            simbox = self.createsimbox(self.getprojectname() + '-BOC-Calculations', isopt = True, createdefault = False)
            sim = self.createsiminsimbox(simbox.getname(), simbox)
            sim.run()   # Make sure simulation is processed, or 'financialanalysis' will not have its D['S'] component. Something to eventually change...
            try:
                testBOCx, testBOCy = simbox.calculateeffectivenesscurve(sim, varfactors)
                print("Project %s has calculated a Budget Objective Curve for..." % self.getprojectname())
                print(varfactors)
            except:
                print("Project %s has failed to produce a Budget Objective Curve for..." % self.getprojectname())
                print(varfactors)
            
            if extendresults:
                self.BOCx.extend(testBOCx)
                self.BOCy.extend(testBOCy)
            else:
                self.BOCx = testBOCx
                self.BOCy = testBOCy
            
            # Keeps the BOC sorted with respect to budget totals (i.e. the x axis).
            self.BOCx, self.BOCy = [list(a) for a in zip(*sorted(zip(self.BOCx, self.BOCy), key=lambda pair: pair[0]))]
            
            self.simboxlist.remove(simbox)      # Deletes temporary SimBoxOpt.
        else:
            print('Budget Objective Curve data already exists for project %s. Proceeding onwards...' % self.getprojectname())
    
    # For now, this is just a complete recalculation of BOC data that already exists. In case you were originally optimising for 1 second or something.
    def recalculateBOC(self):
        if self.hasBOC():
            varfactors = self.converttotalstofactors(self.BOCx)
            
            self.developBOC(varfactors, forcecalc = True)
        else:
            print('Budget Objective Curve data does not seem to exist. Cannot refine.')
    
    # Returns spline for objective values achieved at different budget totals.
    def getBOCspline(self):
        try:
            return pchip(self.BOCx, self.BOCy, extrapolate=True)
        except:
            try:
                return pchip(self.BOCx, self.BOCy) # For backwards compatibility with Numpy 1.8
            except:
                raise Exception('Budget Objective Curve data does not seem to exist...')
        
    def plotBOCspline(self, returnplot = False):
        import matplotlib.pyplot as plt
        from numpy import linspace
        
        try:
            f = self.getBOCspline()
            x = linspace(min(self.BOCx), max(self.BOCx), 200)
            
            fig = plt.figure()
            ax = fig.add_subplot(111)
            
            plt.plot(x,f(x),'-',label='BOC')
            plt.xlabel('Allocation Total')            
            plt.ylabel('Outcome')
            if returnplot:
                return ax
            else:
                plt.legend(loc='best')
                plt.show()
        except:
            print('Plotting of Budget Objective Curve failed!')
        
        return None
        
    def hasBOC(self):
        if len(self.BOCx) == 0 and len(self.BOCy) == 0:
            return False
        else:
            return True
    
    # Useful helper function to convert a summed alloc to a multiplicative factor, ignoring fixed costs.
    def converttotalstofactors(self, totals):
        print('Subtracting fixed costs from budget totals and converting to multiplicative factors...')
        print('A budget total equals non-fixed programs multiplied by the corresponding factor and added to fixed costs.')

        factors = []        
        defaultalloc = self.data['origalloc']        
        
        # Work out which programs don't have an effect and are thus fixed costs (e.g. admin).
        fixedtrue = [1.0]*(len(defaultalloc))
        for i in xrange(len(defaultalloc)):
            if len(self.metadata['programs'][i]['effects']): fixedtrue[i] = 0.0
        fixedtotal = sum([defaultalloc[i]*fixedtrue[i] for i in xrange(len(defaultalloc))])
        vartotal = sum([defaultalloc[i]*(1.0-fixedtrue[i]) for i in xrange(len(defaultalloc))])
        
        for total in totals:
            try:
                factor = (total-fixedtotal)/vartotal
            except:
                print('Divide-by-zero warning: The allocation sum of variable cost programs may be zero.')
                print('Returning a multiplicative budget factor of zero and continuing on...')
                factor = 0.0
            if factor < 0.0:
                print('Budget total $%f is less than the sum of the allocation fixed costs! Not possible.' % total)
                print('Returning a multiplicative budget factor of zero and continuing on...')
                factor = 0.0
            print('Returning a budget multiplication factor of %f for the budget total of $%f.' % (factor, total))
            factors.append(factor)
        
        return factors
    
    # We assume that fixed-cost programs never change. This function returns their sum.
    def returnfixedcostsum(self):
        defaultalloc = self.data['origalloc']        
        
        # Work out which programs don't have an effect and are thus fixed costs (e.g. admin).
        fixedtrue = [1.0]*(len(defaultalloc))
        for i in xrange(len(defaultalloc)):
            if len(self.metadata['programs'][i]['effects']): fixedtrue[i] = 0.0
        fixedtotal = sum([defaultalloc[i]*fixedtrue[i] for i in xrange(len(defaultalloc))])
        
        return fixedtotal

    def printdata(self):
        print(self.data)
    
    def printmetadata(self):
        print(self.metadata)
        
    def printoptions(self):
        print(self.options)
        
    def printprograms(self):
        print(self.metadata['programs'])
        
    def printsimboxlist(self, assubset = False):
        # Prints with nice arrow formats if assubset is true. Otherwise numbers the list.        
        if assubset:
            if len(self.simboxlist) > 0:
                for simbox in self.simboxlist:
                    print(' --> %s%s' % (simbox.getname(), (" (optimisation container)" if isinstance(simbox, SimBoxOpt) else " (standard container)")))
                    simbox.printsimlist(assubsubset = True)
        else:
            if len(self.simboxlist) == 0:
                print('No simulations are currently associated with project %s.' % self.getprojectname())
            else:
                print('Collections of simulations associated with this project...')
                fid = 0
                for simbox in self.simboxlist:
                    fid += 1
                    print('%i: %s%s' % (fid, simbox.getname(), (" (optimisation container)" if isinstance(simbox, SimBoxOpt) else " (standard container)")))
                    simbox.printsimlist(assubsubset = False)
    
    # Generate a new uuid.
    def genuuid(self):
        self.uuid = str(uuid.uuid4())
            
    def setdata(self, data):
        self.data = data
        
    def getdata(self):
        return self.data
        
    def setmetadata(self, metadata):
        self.metadata = metadata
        
    def getmetadata(self):
        return self.metadata
        
    def setoptions(self, options):
        self.options = options
        
    def getoptions(self):
        return self.options
    
    def setprograms(self, programs):
        self.metadata['programs'] = programs
        
    def getprograms(self):
        return self.metadata['programs']
        
    def setprojectname(self, projectname):
        self.metadata['name'] = projectname
        
    def getprojectname(self):
        return self.metadata['name']
     
    def setorigalloc(self, alloc):
        self.data['origalloc'] = alloc
        
    def getorigalloc(self):
        return self.data['origalloc']

    def setD(self, D):
        self.D = D
        
    def getD(self):
        return self.D
        
    def makeworkbook(self,filename):
        """ Generate the Optima workbook -- the hard work is done by makeworkbook.py """
#        from printv import printv
        from dataio import templatepath
        import makeworkbook

        path = templatepath(filename)
        book = makeworkbook.OptimaWorkbook(filename, self.metadata['populations'], self.metadata['programs'], self.metadata['datastart'], self.metadata['dataend'])
        book.create(path)
        
    def loadworkbook(self,filename):
        """ Load an XSLX file into project.data """
        raise Exception('This function is broken temporarily because it does not create a calibration')
        
        import loadworkbook

        # Note
        # 'data' is different depending on whether or not 'programs' is assigned below or not
        # Also, when loading Haiti.xlsx, the variable 'programs' below is different to
        # the contents of D['programs'] obtained by loading 'haiti.json'
        data, programs = loadworkbook.loadworkbook(filename)

        # For now, check that the uploaded programs are the same
        # In future, check project UUID
        if [x['name'] for x in programs] != [x['short_name'] for x in self.metadata['programs']]:
            raise Exception('The programs in the XLSX file do not match the project')

        # Save variables to project
        import updatedata
        self.metadata['programs'] = programs
        self.data = updatedata.getrealcosts(data)
        self.data['current_budget'] = self.data['costcov']['cost']
        
        # Finally, create a calibration from the data.
        simbox = self.createsimbox(self.getprojectname() + '-default-calibration', iscal = True, createdefault = True)
        simbox.calibratefromdefaultdata()
        self.simboxlist.remove(simbox)      # Deletes temporary SimBoxCal.

        if 'meta' not in self.metadata.keys():
            self.metadata['meta'] = self.data['meta']

    def __repr__(self):
        return "Project %s ('%s')" % (self.uuid,self.metadata['name'])

    def get_popidx(self,shortname):
        # Return the index corresponding to a population shortname
        poplist = [x['short_name'] for x in self.metadata['populations']]

        if shortname == 'all':
            return len(poplist)+1
        else:
            try:
                popidx = poplist.index(shortname) + 1 # For some reason (frontend?) these indexes are 1-based rather than 0-based
            except:
                print 'Population "%s" not found! Valid populations are:' % (shortname)
                print poplist
                raise Exception('InvalidPopulation')
            return popidx