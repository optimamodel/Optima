"""
This module defines the classes for stores the results of a single simulation run.

Version: 2015dec09 by cliffk
"""

from optima import uuid, today, getdate, quantile, printv, odict, objectid, dcp
from numpy import array


class Data(object):
    ''' A small class to process data into a form usable for results '''
    
    def __init__(self):
        ''' Create an empty shell of a data structure...'''
        self.pops = None
        self.tot = None
    
    def add(self, parname, data, by):
        ''' Actually add data to the data object '''
        if by=='pops': self.pops = dcp(data) # WARNING, is the dcp() needed?
        elif by=='tot': self.tot = dcp(data) # WARNING, is the dcp() needed?
        else: raise Exception('by="%s" not understood, should be "pops" or "tot"' % by)



class Result(object):
    ''' A tiny class just to hold overall and by-population results '''
    def __init__(self, name=None, isnumber=True, pops=None, tot=None, data=None):
        self.name = name
        self.isnumber = isnumber
        self.pops = pops
        self.tot = tot
        self.data = Data() # An instance of the Data class
        


class Resultset(object):
    ''' Lightweight structure to hold results -- use this instead of a dict '''
    def __init__(self):
        # Basic info
        self.uuid = uuid()
        self.created = today()
        self.project = None
        self.parset = None
        
        # Fundamental quantities
        self.tvec = None
        self.people = None
        
        # Main results -- time series, by population
        self.main = odict() # For storing main results
        self.main['prev'] = Result('HIV prevalence', isnumber=False)
        self.main['force'] = Result('Force-of-infection', isnumber=False)
        self.main['numinci'] = Result('Number of new infections')
        self.main['numplhiv'] = Result('Number of PLHIV')
        self.main['dalys'] = Result('Number of DALYs')
        self.main['numdeath'] = Result('Number of HIV-related deaths')
        self.main['numtreat'] = Result('Number of people on treatment')
        self.main['numdiag'] = Result('Number of people diagnosed')
        self.main['numnewtreat'] = Result('Number of people newly treated')
        self.main['numnewdiag'] = Result('Number of new diagnoses')
        
        # Other quantities
        self.other = odict() # For storing main results
#        self.births = Result()
#        self.mtct = Result()
#        self.newtreat = Result()
#        self.newcircum = Result()
#        self.numcircum = Result()
#        self.reqcircum = Result()
#        self.sexinci = Result()
#    
    
    
    def __repr__(self):
        ''' Print out useful information when called '''
        output = objectid(self)
        output += '      Project name: %s\n'    % (self.project.name if self.project is not None else 'N/A')
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '              UUID: %s\n'    % self.uuid
        return output
    
    
    
    def derivedresults(self, quantiles=None, verbose=2):
        """ Gather standard results into a form suitable for plotting with uncertainties. """
        
        printv('Making derived results...', 3, verbose)
        
        if self.people is None:
            raise Exception('It seems the model has not been run yet, people is empty!')
        
        if quantiles is None: quantiles = [0.5]
        allpeople = array([self.people])
        data = dcp(self.project.data)
        
        self.main['prev'].pops = quantile(allpeople[:,1:,:,:].sum(axis=1) / allpeople[:,:,:,:].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.main['prev'].tot = quantile(allpeople[:,1:,:,:].sum(axis=(1,2)) / allpeople[:,:,:,:].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
        self.main['prev'].data.add('hivprev', data=data, by='pops')
        self.main['prev'].data.add('optprev', data=data, by='tot')
        
        self.main['numplhiv'].pops = quantile(allpeople[:,1:,:,:].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.main['numplhiv'].tot = quantile(allpeople[:,1:,:,:].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
        self.main['numplhiv'].data.add('optplhiv', data=data, by='tot')        
        
        allinci = array([self.inci])
        self.main['numinci'].pops = quantile(allinci, quantiles=quantiles)
        self.main['numinci'].tot = quantile(allinci.sum(axis=1), quantiles=quantiles) # Axis 1 is populations
        self.main['numinci'].data.add('optnuminfect', data=data, by='tot')    

        allinci = array([self.inci])
        self.main['force'].pops = quantile(allinci / allpeople[:,:,:,:].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.main['force'].tot = quantile(allinci.sum(axis=1) / allpeople[:,:,:,:].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
        
        alldeaths = array([self.death])
        self.main['numdeath'].pops = quantile(alldeaths, quantiles=quantiles)
        self.main['numdeath'].tot = quantile(alldeaths.sum(axis=1), quantiles=quantiles) # Axis 1 is populations
        self.main['numdeath'].data.add('optdeath', data=data, by='tot') 

        alldx = array([self.dx])
        self.main['numdiag'].pops = quantile(alldx, quantiles=quantiles)
        self.main['numdiag'].tot = quantile(alldx.sum(axis=1), quantiles=quantiles) # Axis 1 is populations
        self.main['numdiag'].data.add('optnumdiag', data=data, by='tot') 
        

# WARNING, need to implement
#        disutils = [D[self.pars['const']['disutil'][key] for key in D['G['healthstates']]
#        tmpdalypops = allpeople[:,concatenate([D['G['tx1'], D['G['tx2']]),:,:].sum(axis=1) * D['P['const['disutil['tx']
#        tmpdalytot = allpeople[:,concatenate([D['G['tx1'], D['G['tx2']]),:,:].sum(axis=(1,2)) * D['P['const['disutil['tx']
#        for h in xrange(len(disutils)): # Loop over health states
#            healthstates = array([D['G['undx'][h], D['G['dx'][h], D['G['fail'][h]])
#            tmpdalypops += allpeople[:,healthstates,:,:].sum(axis=1) * disutils[h]
#            tmpdalytot += allpeople[:,healthstates,:,:].sum(axis=(1,2)) * disutils[h]
#        self.daly.pops = quantile(tmpdalypops, quantiles=quantiles)
#        self.daly.tot = quantile(tmpdalytot, quantiles=quantiles)
        
        return None # derivedresults()
        

    
    
    