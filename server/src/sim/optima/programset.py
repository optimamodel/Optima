import uuid
from operator import mul
import defaults
from collections import defaultdict
import ccocs
from copy import deepcopy
import liboptima.dataio_binary as dataio_binary
import pylab
import numpy
import simbudget2

coverage_params = ['numcircum','numost','numpmtct','numfirstline','numsecondline'] # This list is copied from makeccocs.py
# What about aidstest, sharing, and breast?

class ProgramSet(object):
    # This class is a collection of programs/modalities
    def __init__(self,name):
        self.name = name
        self.uuid = str(uuid.uuid4())
        self.programs = []
        self.reachability_interaction = 'random' # These are the options on slide 7 of the proposal
        self.current_version = 1

    @classmethod
    def load(ProgramSet,filename,name=None):
        # Use this function to load a ProgramSet saved with ProgramSet.save
        r = ProgramSet(name)
        psetdict = dataio_binary.load(filename)
        r.uuid = psetdict['uuid'] # Loading a ProgramSet restores the original UUID
        r.fromdict(psetdict)
        return r

    def save(self,filename):
        dataio_binary.save(self.todict(),filename)

    @classmethod
    def fromdict(ProgramSet,psetdict):
        p = ProgramSet(None)
        p.name = psetdict['name']
        p.uuid = psetdict['uuid']
        p.programs = [Program.fromdict(x) for x in psetdict['programs']]
        p.reachability_interaction = psetdict['reachability_interaction']
        return p

    def todict(self):
        psetdict = dict()
        psetdict['name'] = self.name 
        psetdict['uuid'] = self.uuid 
        psetdict['programs'] = [x.todict() for x in self.programs]
        psetdict['reachability_interaction'] = self.reachability_interaction 
        psetdict['current_version'] = self.current_version 

        return deepcopy(psetdict)
    
    def __getstate__(self):
        return self.todict()

    def __setstate__(self, state):
        self.fromdict(state)

    def optimizable(self):
        # Return an array the same length as the number of programs
        # containing 'True' if the program has effects and can therefore
        # be optimized
        return [True if prog.coverage_outcome else False for prog in self.programs]

    @classmethod
    def import_legacy(ProgramSet,name,programdata):
        # This function initializes the programs based on the dictionary programdata, obtained
        # from r.metadata['programs']

        ps = ProgramSet(name)
        ps.programs = [] # Make sure we start with an empty program list
        
        for prog in programdata:
            cc_inputs = []
            co_inputs = []

            if prog['effects']: # A spending only program has no effects - it exists in the program list but because it covers no populations, it gets skipped when evaluating parameters
                
                # First, sanitize the population names
                for effect in prog['effects']:
                    if effect['popname'] in ['Total','Average','Overall']:
                        effect['popname'] = 'Overall'

                target_pops = list(set([effect['popname'] for effect in prog['effects']])) # Unique list of affected populations. In legacy programs, they all share the same CC curve
                
                for pop in target_pops:
                    cc_input = dict()
                    cc_input['pop'] = pop
                    if 'scaleup' in prog['ccparams'].keys() and prog['ccparams']['scaleup'] and ~numpy.isnan(prog['ccparams']['scaleup']):
                        cc_input['form'] = 'cc_scaleup'
                    else:
                        cc_input['form'] = 'cc_noscaleup'
                    cc_input['fe_params'] = prog['ccparams']
                    cc_inputs.append(cc_input)

                for effect in prog['effects']:
                    co_input = dict()
                    co_input['pop'] = effect['popname']
                    co_input['param'] = effect['param']

                    if co_input['param'] in coverage_params and co_input['pop'] != 'Overall':
                        # If simbudget2 uses special popsize estimates for the coverage parameters
                        # but this coverage parameter targets a population, then should the population size
                        # or the special estimate be used?
                        raise Exception('A coverage parameter (%s) has been defined for a specific population (%s)? Look into this' % (co_input['param'],co_input['pop']))

                    if effect['param'] in coverage_params: 
                        co_input['form'] = 'identity'
                        co_input['fe_params'] = None
                    else:
                        co_input['form'] = 'co_cofun'
                        co_input['fe_params'] = effect['coparams']
                    
                    co_inputs.append(co_input)

            ps.programs.append(Program(prog['name'],cc_inputs,co_inputs,prog['nonhivdalys']))

        return ps


    def plot(self,pop,par=None,cco=False,show_wait=True):
        # Take in a pop, or a pop and a par
        # Superimpose all curves affecting that quantity

        # First, get a list of all of the programs we are dealing with
        f,ax = pylab.subplots(1,1)

        if par is None: # Plot cost-coverage
            progs = [prog for prog in self.programs if pop in prog.cost_coverage.keys()]

            # Go through and plot coverage for all programs reaching this population
            x = numpy.linspace(0,5e6,100)
            for prog in progs:
                ax.plot(x,prog.get_coverage(pop,x),label=prog.name)
            ax.set_xlabel('Spending ($)')
            ax.set_ylabel('Coverage (fractional)')
        else:
            progs = [prog for prog in self.programs if (pop,par) in prog.get_effects()]
        
            if cco==False: # Plot coverage-outcome
                x = numpy.linspace(0,1,100)
                for prog in progs:
                    ax.plot(x,prog.get_outcome(pop,par,x),label=prog.name)
                ax.set_xlabel('Coverage (fractional)')
                ax.set_ylabel(par)
            else: # Plot cost-coverage-outcome
                x = numpy.linspace(0,5e6,100)
                for prog in progs:
                    cc = prog.get_coverage(pop,x)
                    ax.plot(x,prog.get_outcome(pop,par,cc),label=prog.name)
                ax.set_xlabel('Spending ($)')
                ax.set_ylabel(par)

        ax.legend(loc='lower right')

        if show_wait:
            pylab.show()

        return

    def progs_by_pop(self):
        # Return a dictionary where the keys are all of the populations
        # reached by the programs, and the values are lists of references 
        # to the programs reaching that population 
        # e.g., pops = {'FSW',[<Program 1a04>,<Program a351>]}

        pops = defaultdict(list)
        for prog in self.programs:
            pops_reached = prog.pops()
            for pop in pops_reached:
                pops[pop].append(prog)
        return pops

    def progs_by_effect(self,pop=None):
        # Like progs_by_pop, this function returns a dictionary 
        # like {'condomcas': [Program 6b39 (Condoms & SBCC)], u'hivtest': [Program b127 (HTC)]}
        # These are specific to the population provided as an input argument
        # If no population is specified, then (pop,program) tuples for the parameter are returned instead
        effects = defaultdict(list)
        for prog in self.programs:
            prog_effects = prog.get_effects()
            for effect in prog_effects:
                if pop is None:
                    effects[effect[1]].append((effect[0],prog))
                elif effect[0] == pop: # If the effect applies to the selected population
                    effects[effect[1]].append(prog)
        return effects

    def get_outcomes(self,budget,perturb=False):
        # An alloc is a vector of numbers for each program, that is subject to optimization
        # A budget is spending at a particular time, for each program
        # In the legacy code, we would say 
        #   budget = timevarying.timevarying(alloc)

        # First, we need to know which populations to iterate over
        outcomes = dict()

        pops = self.progs_by_pop();

        for pop in pops.keys():
            progs_reaching_pop = pops[pop]

            # Now get the coverage for this program
            coverage = []
            for prog in progs_reaching_pop:
                spending = budget[self.programs.index(prog),:] # Get the amount of money spent on this program
                coverage.append(prog.get_coverage(pop,spending,perturb)) # Calculate the program's coverage

            # Next, get the list of effects to iterate over
            effects = self.progs_by_effect(pop) 

            #Now we iterate over the effects
            outcomes[pop] = dict()
            for effect in effects.keys():           
                if len(effects[effect]) == 1: # There is no overlapping of modalities
                    prog = effects[effect][0]
                    this_coverage = coverage[progs_reaching_pop.index(prog)] # Get the coverage that this program has for this population
                    assert(effect not in outcomes[pop].keys()) # Multiple programs should not be able to write to the same parameter *without* going through the overlapping calculation
                    outcomes[pop][effect] = prog.get_outcome(pop,effect,this_coverage,perturb) # Get the program outcome and store it in the outcomes dict
                else:
                    print 'OVERLAPPING MODALITIES DETECTED'
                    print 'Pop: %s Effect: %s' % (pop,effect)
                    print 'Programs ',[x.name for x in effects[effect]]
                    print
                    raise Exception('Overlap, coverage distribution, and effect combination go here')
        
        return outcomes

    def get_coverage_legacy(self,spending):
        # This function returns an array of effective coverage values for each metamodality
        # reflow_metamodalities should generally be run before this function is called
        # this is meant to happen automatically when add_modality() or remove_modality is called()
        #
        # Note that coverage is *supposed* to always be in normalized units (i.e. percentage of population)
        # The method program.convert_units() does the conversion to number of people at the last minute
        raise Exception('This code is scheduled for removal')

        if len(self.modalities) == 1:
            spending = array([[spending]]) # Need a better solution...

        assert(len(spending)==len(self.modalities))

        # First, get the temporary coverage for each modality
        for i in xrange(0,len(spending)):
            self.modalities[i].temp_coverage = self.modalities[i].get_coverage(spending[i,:])
        
        print self.modalities[0].temp_coverage

        # Now compute the metamodality coverage
        if self.reachability_interaction == 'random':
            for mm in self.metamodalities:
                mm.temp_coverage1 = reduce(mul,[m.temp_coverage for m in self.modalities if m.uuid in mm.modalities]) # This is the total fraction reached
                
            for i in xrange(len(self.modalities),0,-1): # Iterate over metamodalities containing i modalities
                superset = [mm for mm in self.metamodalities if len(mm.modalities) >= i]
                subset = [mm for mm in self.metamodalities if len(mm.modalities) == i-1]

                for sub in subset:
                    for sup in superset: 
                        if set(sub.modalities).issubset(set(sup.modalities)):
                            sub.temp_coverage1 -= sup.temp_coverage1

        # Next, calculate the coverage for each metamodality
        effective_coverage = [mm.temp_coverage1 for mm in self.metamodalities]
        
        return effective_coverage

    def get_outcomes_legacy(self,effective_coverage):
        raise Exception('This code is scheduled for removal')
        # This function sketches out what the combination of output parameters might be like
        # Each metamodality will return a set of outcomes for its bound effects
        # That is, if the program has 3 effects, each metamodality will return 3 arrays
        # These then need to be combined into the overall program effect on the parameters
        # perhaps using the nonlinear saturating system
        # For coverage programs, the CO curve is the identity function and thus the units
        # are still normalized. De-normalization happens as a third step
        outcomes = []
        for mm,coverage in zip(self.metamodalities,effective_coverage):
            outcomes.append(mm.get_outcomes(self.modalities,coverage))

        # Indexing is outcomes[metamodality][effect][time]
        # Note that outcomes is a list of lists, because the metamodality returns a list of outputs
        # rather than a matrix
        # What we want is outcomes[effect][time]
        # Now we need to merge all of the entries of outcomes into a single outcome. This is done on a per-effect basis

        output_outcomes = []

        for i in xrange(0,len(self.effects['param'])): # For each output effect
            # In this loop, we iterate over the metamodalities and then combine the outcome into a single parameter
            # that is returned for use in D.M
            tmp = outcomes[0][i]
            if len(outcomes) > 1:
                for j in xrange(1,len(outcomes)): # For each metamodality
                    tmp += outcomes[j][i]
            tmp *= (1/len(outcomes))
            output_outcomes.append(tmp)
        #print output_outcomes
        return output_outcomes

    def convert_units(self,output_outcomes,sim_output):
        # This function takes in a set of outcomes (generated by this program) and
        # simobject output e.g. sim_output = sim.run()
        # It iterates over the modalities to find coverage-type modalities
        # It then uses the population sizes in sim_output to convert nondimensional 
        # coverage into numbers of people

        return output_outcomes

    def __getitem__(self,name):
        # Support dict-style indexing based on name e.g.
        # programset.programs[1] might be the same as programset['MSM programs']
        for prog in self.programs:
            if prog.name == name:
                return prog
        print "Available programs:"
        print [prog.name for prog in self.programs]
        raise Exception('Program "%s" not found' % (name))

    def __repr__(self):
        return 'ProgramSet %s (%s)' % (self.uuid[0:4],self.name)

class MetaProgram(object):
    # A metaprogram corresponds to an overlap of programs
    
    # The metamodality knows the coverage (number of people) who fall into the overlapping category
    # The amount of overlap still needs to be specified though
    # For example, if the population size is 100 people, and modality 1 reaches 40, and modality 2 reaches 20,
    # and the metamodality reaches 10, then we know that 10 people are reached by both - 50% of modality 2, and 25% of modality 1
    # So the metamodality coverage is a fraction of the total population
    # And it must be smaller than the smallest coverage for the individual modalities
    def __init__(self,modalities,method='maximum',metamodality=None,overlap=None): # where m1 and m2 are Modality instances
        self.modalities = [m.uuid for m in modalities]

        if metamodality is not None:
            self.modalities += metamodality.modalities # Append the UUIDs from the previous metamodality object

        self.temp_coverage = 0 # This is used internally by program.get_coverage()
        self.method = method

    def get_outcomes(self,modalities,effective_coverage):
        outcomes = []
        for m in modalities:
            if m.uuid in self.modalities:
                outcomes.append(m.get_outcomes(effective_coverage))

        #print 'METAMODALITY'
        # It is indexed
        # outcomes[modality][effect][time]
        # The modality returns an set of outcomes (an array of arrays)
        # Now we need to iterate over them to get a single outcome from the metamodality

        # Suppose the effective_coverage is 0.3. That means that 30% of the population is covered by 
        # ALL of the programs associated with this metamodality. The final outcome can be 
        # combined in different ways depending on the method selected here
        final_outcomes = []
        for i in xrange(0,len(outcomes[0])): # For each output effect
            # In this loop, we iterate over the modalities and then combine the outcome into a single parameter
            # that is returned for use in D.M
            # Each element in outcomes corresponds to 
            tmp = [x[i] for x in outcomes] # These are the outcomes for effect i for each modality
            # tmp is a list of tmp[modality][outcome] for fixed effect. Now we have to iterate over tmp
            if self.method == 'maximum':
                out = tmp[0]
                for j in xrange(1,len(tmp)):
                    out = maximum(out,tmp[j]) # use maximum function from numpy
            final_outcomes.append(out)

        #print final_outcomes
        # Indexing is final_outcomes[effect][time]
        return final_outcomes


    def get_coverage(self,modalities,coverage):
        # Return a list of all of the coverages corresponding to the modalities
        # referred to by this metamodality instance
        # There is one coverage for each modality

        # Note that internally, the coverages are divided equally
        # For example, if the population size is 100 people, and modality 1 is capable of reaching 40, and modality 2 is capable of reaching 20,
        # and the metamodality reaches 10, then we know that 10 people are reached by both. So we set the metamodality maxcoverage
        # to 10 people (0.1). 
        # Now, suppose modality 1 reaches 20 people, and modality 2 reaches 20 people. This mean that of the metamodality now reaches 5 people
        # So we have
        # metamodalitycoverage = (m_1_actualcoverage/m_1_max*m_2_actualcoverage/m_2_max)*self.maxcoverage
        # is the fraction of the total population reached by this combination of programs
        actual_coverage = self.maxcoverage
        for i in xrange(0,len(modalities)):
            if modalities[i].uuid in self.modalities:
                actual_coverage *= coverage[i]/modalities[i].maxcoverage
        return actual_coverage

    def __repr__(self):
        return '(%s)' % (','.join([s[0:4] for s in self.modalities]))

class Program(object):
    # This class is a single modality - a single thing that 
    def __init__(self,name='Default',cc_inputs=[],co_inputs=[],nonhivdalys = 0):
        # THINGS THAT PROGRAMS HAVE
        # frontend quantities
        # functions
        # conversion from FE parameters to BE parameters

        # EXAMPLE INPUTS
        # cc_inputs[0] = dict()
        # cc_inputs[0]['pop'] = 'FSW'
        # cc_inputs[0]['form'] = 'cc_scaleup'
        # cc_inputs[0]['fe_params'] = {u'coveragelower': 0.2, u'nonhivdalys': 0.0, u'funding': 300000.0, u'saturation': 0.98, u'coverageupper': 0.75, u'scaleup': 0.73}

        # co_inputs[0] = dict()
        # co_inputs[0]['pop'] = 'FSW'
        # co_inputs[0]['param'] = 'hivtest'
        # co_inputs[0]['form'] = 'co_cofun'
        # co_inputs[0]['fe_params'] = [0, 0, 2, 2]

        self.name = name        
        self.nonhivdalys = nonhivdalys
        self.uuid = str(uuid.uuid4())
        self.cost_coverage = dict()
        self.coverage_outcome = defaultdict(dict)

        assert(set([x['pop'] for x in cc_inputs]) == set([x['pop'] for x in co_inputs])) # A CC curve must be defined for every population that this program affects

        for cc in cc_inputs:
            cc_class = getattr(ccocs, cc['form']) # This is the class corresponding to the CC form e.g. it could be  a <ccocs.cc_scaleup> object
            assert(cc['pop'] not in self.cost_coverage.keys()) # Each program can only have one CC curve per population
            self.cost_coverage[cc['pop']] = cc_class(cc['fe_params']) # Instantiate it with the CC data, and append it to the program's CC array

        for co in co_inputs:
            co_class = getattr(ccocs, co['form'])
            if isinstance(co['param'],list): # Note that lists cannot be dictionary keys, so [u'condom', u'com'] -> 'condomcom'
                co['param'] = ''.join(co['param'])
            assert(co['pop'] not in self.coverage_outcome.keys() or co['param'] not in self.coverage_outcome[co['pop']].keys()) # Each program can only have one CO curve per effect
            self.coverage_outcome[co['pop']][co['param']] = co_class(co['fe_params']) # Instantiate it with the CC data, and append it to the program's CC array

    @classmethod
    def fromdict(Program,programdict):
        p = Program()
        p.name = programdict['name']
        p.nonhivdalys = programdict['nonhivdalys']
        p.uuid = programdict['uuid']
        for pop in programdict['cost_coverage'].keys():
            p.cost_coverage[pop] = ccocs.ccoc.fromdict(programdict['cost_coverage'][pop])
        for pop in programdict['coverage_outcome'].keys():
            for par in programdict['coverage_outcome'][pop].keys():
                p.coverage_outcome[pop][par] = ccocs.ccoc.fromdict(programdict['coverage_outcome'][pop][par])
        return p

    def todict(self):
        programdict = dict()
        programdict['name'] = self.name 
        programdict['nonhivdalys'] = self.nonhivdalys 
        programdict['uuid'] = self.uuid 
        programdict['cost_coverage'] = dict()
        programdict['coverage_outcome'] = defaultdict(dict)
        for pop in self.cost_coverage.keys():
            programdict['cost_coverage'][pop] = self.cost_coverage[pop].todict()
        for pop in self.coverage_outcome.keys():
            for par in self.coverage_outcome[pop].keys():
                programdict['coverage_outcome'][pop][par] = self.coverage_outcome[pop][par].todict()
        return deepcopy(programdict)

    def pops(self):
        # Return a list of populations covered by this program
        return [p for p in self.coverage_outcome.keys() if p is not None]

    def get_effects(self):
        # Returns a list of tuples storing effects as (population,parameter)
        effects = []
        for pop in self.pops():
            for param in self.coverage_outcome[pop].keys():
                effects.append((pop,param))
        return effects

    def get_coverage(self,pop,spending,perturb=False):
        # Return the coverage of a particular population given the spending amount
        return self.cost_coverage[pop].evaluate(spending,perturb)

    def get_outcome(self,pop,effect,coverage,perturb=False):
        # Return the outcome for a particular effect given the parent population's coverage
        if isinstance(effect,list):
            effect = ''.join(effect)
        return self.coverage_outcome[pop][effect].evaluate(coverage,perturb)

    def plot(self,sim=None,show_wait=True):
        # # This function will just plot everything
        # First, plot coverages
        # Then plot a column of outcomes
        # Then plot a column of coverage-outcomes

        # how many pops 
        n_pops = len(self.cost_coverage.keys())
        n_pars = sum([len(self.coverage_outcome[x].keys()) for x in self.cost_coverage.keys()])
        n_rows = max(n_pops,n_pars)

        if n_rows == 0:
            print 'Program %s is spending only' % (self.name)
            return

        # Set up the figure
        if self.cost_coverage.keys() == ['Overall']: # coverage program
            f, axarr = pylab.subplots(n_pops, 1,figsize=(24,16))
        else:
            f, axarr = pylab.subplots(n_rows, 3,figsize=(24,16))
        f.tight_layout()
        f.canvas.set_window_title(self.name)
        # f.set_size_inches(100,100)

        if not isinstance(axarr,numpy.ndarray): # A 1x1 subplot returns an axis, not a list of axes
            axarr = numpy.array([[axarr]])

        # Plot populations
        count = 0
        for pop in self.cost_coverage.keys():
            # Go down the first column
            self.plot_single(pop,ax=axarr[count,0],sim=sim,show_wait=False)
            count += 1

        # Delete extra rows
        while count < n_rows:
            f.delaxes(axarr[count,0])
            count += 1

        # If no effects, return now
        if axarr.shape[0] == 1:
            if show_wait:
                pylab.show()
            return

        # Next, plot the coverages and effects
        count = 0
        for pop in self.cost_coverage.keys():
            for par in self.coverage_outcome[pop].keys():
                self.plot_single(pop,par,cco=False,sim=sim,ax=axarr[count,1],show_wait=False)
                self.plot_single(pop,par,cco=True,sim=sim,ax=axarr[count,2],show_wait=False)
                count += 1

        if show_wait:
            pylab.show()

        return

    def plot_single(self,pop=None,par=None,cco=False,sim=None,show_wait=True,ax=None):
        # Make a single plot of one of the CCOC objects
        # USAGE
        # - specify a population and no par to see cost-coverage
        # - specify a population and an par to see coverage-outcome
        # - specify a population and an par and cco=True to see the CCO curve
        # The x and y values will be returned. Plot will be generated by default
        if ax is None:
            f,ax = pylab.subplots(1,1)

        if sim is not None:
            # What is the index of this program in the alloc/budget?
            p = sim.getproject()

            if not sim.isinitialised():
                sim.initialise()

            prog_index = [a.name for a in sim.getprogramset().programs].index(self.name)
            prog_start_index = numpy.argmin(numpy.abs(sim.program_start_year-sim.default_pars['tvec'])) if numpy.isfinite(sim.program_start_year) else None
            prog_end_index = numpy.argmin(numpy.abs(sim.program_end_year-sim.default_pars['tvec'])) if numpy.isfinite(sim.program_end_year) else None
            datacost = p.data['ccocs'][self.name]['cost']
            cost_x_limit = max(max(sim.budget[prog_index,:]),numpy.nanmax(datacost))*2
            popnumber = [a['short_name'] for a in p.metadata['inputpopulations']].index(pop)
        else:
            cost_x_limit = 1e6

        if par is None:
            x_limit = cost_x_limit

            # And then plot the CC curve
            x = numpy.linspace(0,x_limit,100)
            y = self.cost_coverage[pop].evaluate(x) 
            yl = self.cost_coverage[pop].evaluate(x,bounds='lower') 
            yu = self.cost_coverage[pop].evaluate(x,bounds='upper') 

            if sim is not None:
                # Get the program data
                datacost = p.data['ccocs'][self.name]['cost']
                datacoverage = get_data_coverage(self.name,pop,sim)
                ax.scatter(datacost,datacoverage,color='#666666',zorder=8)

                # What is the alloc for this program?
                # Let's go with the upper and lower bounds of the budget for this program
                if prog_start_index is not None:
                    ax.axvline(x=sim.budget[prog_index,prog_start_index], color='red',zorder=9)
                if prog_end_index is not None:
                    ax.axvline(x=sim.budget[prog_index,prog_end_index], color='blue',zorder=8)


        elif not cco:  
            # coverage-outcome plot
            x_limit = 1          
            x = numpy.linspace(0,x_limit,100)
            y = self.coverage_outcome[pop][par].evaluate(x) # plot coverage-outcome
            yl = self.coverage_outcome[pop][par].evaluate(x,bounds='lower') 
            yu = self.coverage_outcome[pop][par].evaluate(x,bounds='upper') 

            if sim is not None:
                # First, get the outcome and coverage
                # First, find the population index
                dataoutcome = get_data_outcome(pop,par,sim)

                if len(dataoutcome) == 1:
                    ax.axhline(dataoutcome[0], color='#666666',zorder=8)
                else:
                    datacoverage = get_data_coverage(self.name,pop,sim)
                    ax.scatter(datacoverage,dataoutcome,color='#666666',zorder=8)

                if prog_start_index is not None:
                    ax.axvline(x=self.cost_coverage[pop].evaluate(sim.budget[prog_index,prog_start_index]), color='red',zorder=9)
                    ax.axhline(y=sim.default_pars[par][popnumber,prog_start_index], color='red',zorder=9)

                if prog_end_index is not None:
                    ax.axvline(x=self.cost_coverage[pop].evaluate(sim.budget[prog_index,prog_end_index]), color='blue',zorder=8)
                    ax.axhline(y=sim.default_pars[par][popnumber,prog_end_index], color='blue',zorder=9)

        else:
            x_limit = cost_x_limit

            x = numpy.linspace(0,x_limit,100)
            cc = self.cost_coverage[pop].evaluate(x)
            ccl = self.cost_coverage[pop].evaluate(x,bounds='lower') 
            ccu =self.cost_coverage[pop].evaluate(x,bounds='upper') 
            y = self.coverage_outcome[pop][par].evaluate(cc)
            yl = self.coverage_outcome[pop][par].evaluate(ccl,bounds='lower') 
            yu =self.coverage_outcome[pop][par].evaluate(ccu,bounds='upper') 

            if sim is not None:
                datacost = p.data['ccocs'][self.name]['cost']
                dataoutcome = get_data_outcome(pop,par,sim)
                if len(dataoutcome) == 1:
                    ax.axhline(dataoutcome[0], color='#666666',zorder=8)
                else:
                    ax.scatter(datacost,dataoutcome,color='#666666',zorder=8)


                if par in sim.default_pars:

                    def overlay_scatters(index,color,order):
                        spending_at_time = sim.budget[prog_index,index]
                        datapar_at_time = sim.default_pars[par][popnumber,index]
                        cc_at_time = self.cost_coverage[pop].evaluate(spending_at_time)
                        modelpar_at_time = self.coverage_outcome[pop][par].evaluate(cc_at_time)
                        ax.axvline(spending_at_time, color=color,zorder=order)
                        ax.axhline(datapar_at_time, color=color,zorder=order)
                        ax.scatter([spending_at_time,spending_at_time],[datapar_at_time,modelpar_at_time],color=color,zorder=order)

                    if prog_start_index is not None:
                        overlay_scatters(prog_start_index,'red',9)
                    if prog_end_index is not None:
                        overlay_scatters(prog_end_index,'blue',8)

                else:
                    if prog_start_index is not None:
                        ax.axvline(sim.budget[prog_index,prog_start_index], color='red',zorder=9)
                    if prog_end_index is not None:
                        ax.axvline(sim.budget[prog_index,prog_stop_index], color='blue',zorder=8)



        ax.plot(x,y,linestyle='-',color='#a6cee3',linewidth=2)
        ax.plot(x,yl,linestyle='--',color='#000000',linewidth=2)
        ax.plot(x,yu,linestyle='--',color='#000000',linewidth=2)
        ax.set_xlim([0,x_limit])

        if par is None:
            ax.set_xlabel('Spending ($)')
            ax.set_ylabel('Coverage (fractional)')
            ax.set_title(pop)
            ax.set_ylim([0,1])
        elif not cco:
            ax.set_xlabel('Coverage (fractional)')
            ax.set_ylabel(par)
            ax.set_title(pop+'-'+par)
        else:
            ax.set_xlabel('Spending ($)')
            ax.set_ylabel(par)
            ax.set_title(pop+'-'+par)

        if show_wait:
            pylab.show()

    def __repr__(self):
        return 'Program %s (%s)' % (self.uuid[0:4],self.name)

def get_data_coverage(progname,targetpop,sim):
    p = sim.getproject()

    datacoverage = p.data['ccocs'][progname]['coverage']
    epiyears = p.data['epiyears'] # The corresponding years

    if len(datacoverage)==1:
        datacoverage = datacoverage*numpy.ones(epiyears.shape)

    # Rescale the coverage according to the population size estimate
    if numpy.any(datacoverage > 1): # Only rescale if not percentages
        for i in range(len(datacoverage)): 
            if numpy.isfinite(datacoverage[i]):
                matching_index = numpy.argmin(numpy.abs(epiyears[i]-sim.popsizes['tvec']))
                datacoverage[i] /= sim.popsizes[targetpop][matching_index]

    return datacoverage

def get_data_outcome(pop,par,sim):
    p = sim.getproject()
    popnumber = [a['short_name'] for a in p.metadata['inputpopulations']].index(pop)

    # Now, find the data for this program
    for partype in p.data.keys():
        if par in p.data[partype]:
            dataoutcome = p.data[partype][par][popnumber]
            return dataoutcome

    raise Exception('Parameter %s not found' % (par))
