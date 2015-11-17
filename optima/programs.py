"""
This module defines the Program and Response classes, which are 
used to define a single program/modality (e.g., FSW programs) and a 
set of programs, respectively.

Version: 2015nov04 by robynstuart
"""
from utils import getdate, today, uuid, printv
from collections import defaultdict
import abc

class Programset(object):

    def __init__(self, name='default',programs=None):
        ''' Initialize '''
        self.name = name
        self.id = uuid()
        self.programs = {program.name: program for program in programs.values()} if programs else {}
        self.gettargetpops() if programs else []
        self.gettargetpars() if programs else []
        self.gettargetpartypes() if programs else []
        self.initialize_covout() if programs else []
        self.created = today()
        self.modified = today()

    def __repr__(self):
        ''' Print out useful information'''
        output = '\n'
        output += '       Response name: %s\n'    % self.name
        output += '            Programs: %s\n'    % [prog.name for prog in self.programs.values()]
        output += 'Targeted populations: %s\n'    % self.targetpops
        output += '        Date created: %s\n'    % getdate(self.created)
        output += '       Date modified: %s\n'    % getdate(self.modified)
        output += '                  ID: %s\n'    % self.id
        return output

    def gettargetpops(self):
        '''Lists populations targeted by some program in the response'''
        self.targetpops = []
        if self.programs:
            for prog in self.programs.values():
                for x in prog.targetpops: self.targetpops.append(x)
            self.targetpops = list(set(self.targetpops))
    
    def gettargetpars(self):
        '''Lists model parameters targeted by some program in the response'''
        self.targetpars = []
        if self.programs:
            for prog in self.programs.values():
                for x in prog.targetpars: self.targetpars.append(x)

    def gettargetpartypes(self):
        '''Lists model parameters targeted by some program in the response'''
        self.targetpartypes = []
        if self.programs:
            for prog in self.programs.values():
                for x in prog.targetpartypes: self.targetpartypes.append(x)
            self.targetpartypes = list(set(self.targetpartypes))

    def initialize_covout(self):
        '''Initializes the required coverage-outcome curves.
           Parameters for actually defining these should be added using 
           R.covout[paramtype][parampop].addccopar()'''
        self.gettargetpops()
        self.covout = {}
        for targetpartype in self.targetpartypes:
            self.covout[targetpartype] = {}
            for targetpop in self.progs_by_targetpar(targetpartype).keys():
                targetingprogs = [x.name for x in self.progs_by_targetpar(targetpartype)[targetpop]]                
                initccoparams = {k: [] for k in targetingprogs}
                initccoparams['t'],initccoparams['intercept'] = [], []
                self.covout[targetpartype][targetpop] = Covout(initccoparams)                

    def addprog(self,newprog):
        if newprog not in self.programs.keys():
            self.programs[newprog.keys()[0]] = newprog.values()[0]
            self.gettargetpops()
            self.gettargetpartypes()
            self.initialize_covout()
            print('\nAdded program "%s" to programset "%s". \nPrograms in this programset are: %s' % (newprog.keys()[0], self.name, [p.name for p in self.programs.values()]))
        else:
            raise Exception('Program "%s" is already present in programset "%s".' % (newprog.name, self.name))
        
    def rmprog(self,prog):
        if prog not in self.programs.keys():
            raise Exception('You have asked to remove program "%s", but there is no program by this name in programset "%s". Available programs are' % (prog.name, self.name, [p.name for p in self.programs.values()]))
        else:
            del self.programs[prog]
            self.gettargetpops()
            self.gettargetpartypes()
            self.initialize_covout()
            print('\nRemoved program "%s" from programset "%s". \nPrograms in this programset are: %s' % (prog, self.name, [p.name for p in self.programs.values()]))
        
    def optimizable(self):
        return [True if prog.targetpars else False for prog in self.programs.values()]

    def progs_by_targetpop(self, filter_pop=None):
        '''Return a dictionary with:
             keys: all populations targeted by programs
             values: programs targeting that population '''
        progs_by_targetpop = defaultdict(list)
        for prog in self.programs.values():
            targetpops = prog.targetpops if prog.targetpops else None
            if targetpops:
                for targetpop in targetpops:
                    progs_by_targetpop[targetpop].append(prog)
        if filter_pop: return dict(progs_by_targetpop)[filter_pop]
        else: return dict(progs_by_targetpop)
            
    def progs_by_targetpartype(self, filter_partype=None):
        '''Return a dictionary with:
             keys: all populations targeted by programs
             values: programs targeting that population '''
        progs_by_targetpartype = defaultdict(list)
        for prog in self.programs.values():
            targetpartypes = prog.targetpartypes if prog.targetpartypes else None
            if targetpartypes:
                for targetpartype in targetpartypes :
                    progs_by_targetpartype[targetpartype].append(prog)
        if filter_partype: return dict(progs_by_targetpartype)[filter_partype]
        else: return dict(progs_by_targetpartype)

    def progs_by_targetpar(self, filter_partype=None):
        '''Return a dictionary with:
             keys: all populations targeted by programs
             values: programs targeting that population '''
        progs_by_targetpar = {}
        for targetpartype in self.targetpartypes:
            progs_by_targetpar[targetpartype] = defaultdict(list)
            for prog in self.progs_by_targetpartype(targetpartype):
                targetpars = prog.targetpars if prog.targetpars else None
                for targetpar in targetpars:
                    if targetpartype==targetpar['param']: progs_by_targetpar[targetpartype][targetpar['pop']].append(prog)
            progs_by_targetpar[targetpartype] = dict(progs_by_targetpar[targetpartype])
        if filter_partype: return dict(progs_by_targetpar)[filter_partype]
        else: return dict(progs_by_targetpar)
            
    def targetpars_by_prog(self,filter_prog=None):
        '''Return a dictionary with:
             keys: all programs
             values: all model parameters targeted by that program'''
        targetpars_by_prog = {}
        progs_by_targetpop = self.progs_by_targetpop()
        for targetpop in progs_by_targetpop.keys():
            for prog in progs_by_targetpop[targetpop]:
                targetpars_by_prog[prog.name] = defaultdict(list)
                for targetpar in prog.targetpars:
                    targetpars_by_prog[prog.name][targetpar['pop']].append(targetpar['param'])
                targetpars_by_prog[prog.name] = dict(targetpars_by_prog[prog.name])
        if filter_prog: return targetpars_by_prog[filter_prog]
        else: return targetpars_by_prog

    def getprogcoverage(self,budget,t,P,parsetname,perturb=False,verbose=2):
        '''Budget is currently assumed to be a DICTIONARY OF ARRAYS'''        
        coverage = {}       
        for prog in self.programs.keys():
            if self.programs[prog].optimizable():
                if not self.programs[prog].costcovfn.ccopars:
                    printv('WARNING: no cost-coverage function defined for optimizable program, setting coverage to None...', 1, verbose)
                    coverage[prog] = None
                else:
                    spending = budget[prog] # Get the amount of money spent on this program
                    coverage[prog] = self.programs[prog].getcoverage(x=spending,t=t,P=P,parsetname='default') # Two equivalent ways to do this, probably redundant  
            else: coverage[prog] = None
        return coverage
        
    def getpopcoverage(self,budget,t,P,parsetname,perturb=False,verbose=2):
        '''Get the number of people from each population covered by each program...'''
        popcoverage = {}
        
        for prog in self.programs.keys():
            if self.programs[prog].optimizable():
                if not self.programs[prog].costcovfn.ccopars:
                    printv('WARNING: no cost-coverage function defined for optimizable program, setting coverage to None...', 1, verbose)
                    popcoverage[prog] = None
                else:
                    spending = budget[prog] # Get the amount of money spent on this program
                    popcoverage[prog] = self.programs[prog].getcoverage(x=spending,t=t,P=P,parsetname='default',total=False) # Two equivalent ways to do this, probably redundant  
            else: popcoverage[prog] = None
        return popcoverage

    def getoutcomes(self,tvec,budget,perturb=False):
        outcomes = dict()
        
        # First, disaggregate the coverage...
        
        return outcomes

class Program(object):
    ''' Defines a single program. 
    Can be initialized with:
    ccpars, e.g. {'t': [2015,2016], 'saturation': [.90,1.], 'unitcost': [40,30]}
    modelpars, e.g. [{'param': 'hivtest', 'pop': 'FSW'}, {'param': 'hivtest', 'pop': 'MSM'}]'''

    def __init__(self,name,targetpars=None,targetpops=None,ccopars=None,costcovdata=None,nonhivdalys=0):
        '''Initialize'''
        self.name = name
        self.id = uuid()
        self.targetpars = targetpars if targetpars else []            
        self.targetpops = targetpops if targetpops else []
        self.targetpartypes = list(set([x['param'] for x in targetpars])) if targetpars else []
        self.optimizable()
        self.costcovfn = Costcov(ccopars=ccopars)
        self.costcovdata = costcovdata if costcovdata else {'t':[],'cost':[],'coverage':[]}
        
    def __repr__(self):
        ''' Print out useful info'''
        output = '\n'
        output += '          Program name: %s\n'    % self.name
        output += '  Targeted populations: %s\n'    % self.targetpops 
        output += '   Targeted parameters: %s\n'    % self.targetpars 
        output += '\n'
        return output

    def optimizable(self):
        return True if self.targetpars else False

    def addtargetpar(self,targetpar):
        '''Add a model parameter to be targeted by this program'''
        if targetpar not in self.targetpars:
            self.targetpars.append(targetpar)
            self.optimizable
            print('\nAdded target parameter "%s" to the list of target parameters affected by "%s". \nAffected parameters are: %s' % (targetpar, self.name, self.targetpars))
        else:
            raise Exception('The target parameter you are trying to add is already present in the list of target parameters affected by this program:%s.' % self.targetpars)
        return None
        
    def rmtargetpar(self,targetpar):
        '''Remove a model parameter from those targeted by this program'''
        if targetpar not in self.targetpars:
            raise Exception('The target parameter you have selected for removal is not in the list of target parameters affected by this program:%s.' % self.targetpars)
        else:
            self.targetpars.pop(self.targetpars.index(targetpar))
            self.optimizable
            print('\nRemoved model parameter "%s" from the list of model parameters affected by "%s". \nAffected parameters are: %s' % (targetpar, self.name, self.targetpars))
        return None
        
    def addcostcovdatum(self,costcovdatum,overwrite=False):
        '''Add cost-coverage data point'''
        if costcovdatum['t'] not in self.costcovdata['t']:
            self.costcovdata['t'].append(costcovdatum['t'])
            self.costcovdata['cost'].append(costcovdatum['cost'])
            self.costcovdata['coverage'].append(costcovdatum['coverage'])
            print('\nAdded cc data "%s" to program: "%s". \nCC data for this program are: %s' % (costcovdatum, self.name, self.costcovdata))
        else:
            if overwrite:
                ind = self.costcovdata['t'].index(int(costcovdatum['t']))
                oldcostcovdatum = {'t':self.costcovdata['t'][ind],'cost':self.costcovdata['cost'][ind],'coverage':self.costcovdata['coverage'][ind]}
                self.costcovdata['t'][ind] = costcovdatum['t']
                self.costcovdata['cost'][ind] = costcovdatum['cost']
                self.costcovdata['coverage'][ind] = costcovdatum['coverage']
                newcostcovdatum = {'t':self.costcovdata['t'][ind],'cost':self.costcovdata['cost'][ind],'coverage':self.costcovdata['coverage'][ind]}
                print('\nModified cc data from "%s" to "%s" for program: "%s". \nCC data for this program are: %s' % (oldcostcovdatum, newcostcovdatum, self.name, self.costcovdata))
            else:
                raise Exception('You have already entered cost and/or coverage data for the year %s .' % costcovdatum['t'])

    def rmcostcovdatum(self,year):
        '''Remove cost-coverage data point. The point to be removed can be specified by year (int or float).'''
        if int(year) in self.costcovdata['t']:
            self.costcovdata['cost'].pop(self.costcovdata['t'].index(int(year)))
            self.costcovdata['coverage'].pop(self.costcovdata['t'].index(int(year)))
            self.costcovdata['t'].pop(self.costcovdata['t'].index(int(year)))
            print('\nRemoved cc data in year "%s" from program: "%s". \nCC data for this program are: %s' % (year, self.name, self.costcovdata))
        else:
            raise Exception('You have asked to remove data for the year %s, but no data was added for that year. Cost coverage data are: %s' % (year, self.costcovdata))

    def gettargetpopsize(self,t,P,parsetname,total=True):
        '''Returns coverage in a given year for a given spending amount. Currently assumes coverage is a proportion.'''
        from numpy import array

        # Figure out input data type, transform if necessary
        if isinstance(t,(float,int)): t = 'singleyear'
        elif isinstance(t,list): t = array(t)

        # Sum the target populations
        targetpopsize = {}
        allpops = getpopsizes(P=P,parsetname=parsetname,years=t)
        for targetpop in self.targetpops:
            targetpopsize[targetpop] = allpops[targetpop]
        if total: return sum(targetpopsize.values())
        else: return targetpopsize

    def getcoverage(self,x,t,P,parsetname,targetpopprop=None,total=True,proportion=False):
        '''Returns coverage in a given year for a given spending amount'''
        from numpy import transpose
        poptargeted = self.gettargetpopsize(t=t,P=P,parsetname=parsetname,total=False)
        totaltargeted = sum(poptargeted.values())
        totalreached = self.costcovfn.evaluate(x,totaltargeted,t)
        
        popreached = {}
        if not total and not targetpopprop: # calculate targeting since it hasn't been provided
            targetpopprop = {}
            for targetpop in self.targetpops:
                targetpopprop[targetpop] = poptargeted[targetpop]/totaltargeted
                popreached[targetpop] = transpose(transpose(totalreached)*targetpopprop[targetpop]/transpose(totaltargeted)) # Obviously need to fix this

        if total: return transpose(transpose(totalreached)/totaltargeted) if proportion else totalreached
        else: return popreached
        
class CCOF(object):
    '''Cost-coverage, coverage-outcome and cost-outcome objects'''
    __metaclass__ = abc.ABCMeta

    def __init__(self,ccopars=None):
        self.ccopars = ccopars

    def __repr__(self):
        ''' Print out useful info'''
        output = '\n'
        output += 'Programmatic parameters: %s\n'    % self.ccopars
        output += '\n'
        return output

    def addccopar(self,ccopar,overwrite=False):
        ''' Add or replace parameters for cost-coverage functions'''

        if ccopar.get('unitcost') and not ccopar.get('saturation'): ccopar['saturation'] = 1.

        if self.ccopars is None:
            self.ccopars = {}
            for ccopartype in ccopar.keys():
                self.ccopars[ccopartype] = [ccopar[ccopartype]]
        else:
            if (not self.ccopars['t']) or (ccopar['t'] not in self.ccopars['t']):
                for ccopartype in self.ccopars.keys():
                    self.ccopars[ccopartype].append(ccopar[ccopartype])
                print('\nAdded CCO parameters "%s". \nCCO parameters are: %s' % (ccopar, self.ccopars))
            else:
                if overwrite:
                    ind = self.ccopars['t'].index(int(ccopar['t']))
                    oldccopar = {}
                    for ccopartype in self.ccopars.keys():
                        oldccopar[ccopartype] = self.ccopars[ccopartype][ind]
                        self.ccopars[ccopartype][ind] = ccopar[ccopartype]
                    print('\nModified CCO parameter from "%s" to "%s". \nCCO parameters for are: %s' % (oldccopar, ccopar, self.ccopars))
                else:
                    raise Exception('You have already entered CCO parameters for the year %s. If you want to overwrite it, set overwrite=True when calling addccopar().' % ccopar['t'])
        return None

    def rmccopar(self,t):
        '''Remove cost-coverage-outcome data point. The point to be removed can be specified by year (int or float).'''
        if isinstance(t,int) or isinstance(t,float):
            if int(t) in self.ccopars['t']:
                ind = self.ccopars['t'].index(int(t))
                for ccopartype in self.ccopars.keys():
                    self.ccopars[ccopartype].pop(ind)
                print('\nRemoved CCO parameters in year "%s". \nCCO parameters are: %s' % (t, self.ccopars))
            else:
                raise Exception('You have asked to remove CCO parameters for the year %s, but no data was added for that year. Available parameters are: %s' % (t, self.ccopars))            
        return None

    def getccopar(self,t,randseed=None,bounds=None):
        '''Get a cost-coverage-outcome parameter set for any year in range 1900-2100'''
        from utils import smoothinterp, findinds
        from numpy import array, arange, zeros
        from copy import deepcopy
        
        # Error checks
        if not self.ccopars:
            raise Exception('Need parameters for at least one year before function can be evaluated.')            
        if randseed and bounds:
            raise Exception('Either select bounds or specify randseed')            

        # Set up necessary variables
        ccopar = {}
        if isinstance(t,(float,int)): t = [t]
        nyrs = len(t)
        ccopars_no_t = deepcopy(self.ccopars)
        del ccopars_no_t['t']
        ccopartuples = sorted(zip(self.ccopars['t'], *ccopars_no_t.values()))
        knownt = array([ccopartuple[0] for ccopartuple in ccopartuples])
        allt = arange(1900,2100)
        j = 1
        
        # Calculate interpolated parameters
        for param in ccopars_no_t.keys():
            knownparam = array([ccopartuple[j] for ccopartuple in ccopartuples])
            allparams = smoothinterp(allt, knownt, knownparam, smoothness=1)
            ccopar[param] = zeros(nyrs)
            for yr in range(nyrs):
                ccopar[param][yr] = allparams[findinds(allt,t[yr])]
            if isinstance(t,list): ccopar[param] = ccopar[param].tolist()
            j += 1

        ccopar['t'] = t
        return ccopar

    def evaluate(self,x,popsize,t,randseed=None,bounds=None):
        ccopar = self.getccopar(t,randseed,bounds)
        return self.function(x,ccopar,popsize)

    @abc.abstractmethod # This method must be defined by the derived class
    def emptypars(self):
        pass

    @abc.abstractmethod # This method must be defined by the derived class
    def function(self,x,ccopar,popsize):
        pass

######## SPECIFIC CCOF IMPLEMENTATIONS
class Costcov(CCOF):
    '''Cost-coverage objects'''
            
    def function(self,x,ccopar,popsize):
        '''Returns coverage in a given year for a given spending amount. Currently assumes coverage is a proportion.'''
        from numpy import exp, zeros, array
        u = ccopar['unitcost']
        s = ccopar['saturation']
        if isinstance(x,(float,int)): typex, x = 'single',array([x])
        if isinstance(popsize,(float,int)): popsize = array([popsize])
        else: typex = 'multiple'
        nyrs,npts = len(u),len(x)
        y = zeros((nyrs,npts))
        for yr in range(nyrs):
            y[yr,:] = (2*s[yr]/(1+exp(-2*x/(popsize[yr]*s[yr]*u[yr])))-s[yr])*popsize[yr]
        return y if not typex=='single' else y[0]     

    def emptypars(self):
        ccopars = {}
        ccopars['saturation'] = None
        ccopars['unitcost'] = None
        ccopars['t'] = None
        return ccopars                        

class Covout(CCOF):
    '''Coverage-outcome objects'''

    def function(self,x,ccopar,popsize):
        ''' Returns outcome given parameters'''
        









#    def function(self,x,ccopar,popsize):
#        '''Returns coverage in a given year for a given spending amount. Currently assumes coverage is a proportion.'''
#        from numpy import array
#        i = ccopar['intercept'][0]
#        g = ccopar['gradient'][0]
#        y = i + (x*g)/popsize
#        if isinstance(y,float): return min(y,1)
#        else: return array([min(j,1) for j in y]) 
      
    def emptypars(self):
        ccopars = {}
        ccopars['intercept'] = None
        ccopars['gradient'] = None
        ccopars['t'] = None
        return ccopars                        


#######################################################
# What needs to happen to get population sizes...
#######################################################

def getpopsizes(P, parsetname, years, filter_pop=None):
    '''Get population sizes in given years from a parset.'''
    from utils import findinds
    from numpy import array, zeros
    
    if isinstance(years,(float,int)): years = array([[years]])
    elif isinstance(years,list): years = array([years])
    
    initpopsizes = P.parsets[parsetname].interp(start=min(years), end=max(years), filter_param='popsize')
    tvec = P.parsets[parsetname].interp(start=min(years), end=max(years), filter_param='tvec') # TODO: calling this twice is stupid.
    popsizes = {}

    for popnumber, pop in enumerate(P.data['pops']['short']):
        popsizes[pop] = zeros(len(years))
        for yrno, yr in enumerate(years):
            popsizes[pop][yrno] = initpopsizes[popnumber,findinds(tvec,yr)[0]]

    if filter_pop: return {filter_pop: popsizes[filter_pop]}
    else: return popsizes
   
