"""
GATHERPLOTDATA

This file gathers all data that could be used for plotting and packs it into a
nice little convenient structure :)

Version: 2015feb04 by cliffk
"""

# Define labels
epititles = {'prev':'Prevalence', 'plhiv':'PLHIV', 'inci':'New infections', 'force':'Incidence', 'daly':'DALYs', 'death':'Deaths', 'dx':'Diagnoses', 'tx1':'First-line treatment', 'tx2':'Subsequent lines of treatment'}
epiylabels = {'prev':'HIV prevalence (%)', 'plhiv':'Number of PLHIV', 'inci':'New HIV infections per year', 'force':'Incidence per 100 person-years', 'daly':'HIV-related DALYs per year', 'death':'HIV/AIDS-related deaths per year', 'dx':'New HIV diagnoses per year', 'tx1':'People on first-line treatment', 'tx2':'People on subsequent lines of treatment'}
costtitles = {'costcum':'Cumulative HIV-related financial costs'}
costylabels = {}

def gatheruncerdata(D, R, annual=True, verbose=2, maxyear=2030):
    """ Gather standard results into a form suitable for plotting with uncertainties. """
    from numpy import zeros, nan, size, ndim, array, asarray
    from liboptima.utils import printv
    from copy import deepcopy
    printv('Gathering epidemiology results...', 3, verbose)
    
    uncer = dict()
    uncer['tvec'] = R['tvec'].tolist() # Copy time vector
    uncer['poplabels'] = D['G']['meta']['pops']['short']
    uncer['colorm'] = (0,0.3,1) # Model color
    uncer['colord'] = (0,0,0) # Data color
    uncer['legend'] = ('Model', 'Data')
    uncer['xdata'] = D['data']['epiyears']
    ndatayears = len(uncer['xdata'])
    
    # Downsample to annual
    origtvec = deepcopy(uncer['tvec'])
    if annual:
        dt = origtvec[1]-origtvec[0]
        allindices = range(0, len(origtvec), int(round(1/dt)))
        indices = []
        for i in allindices:
            if origtvec[i]<=maxyear:
                indices.append(i)
        uncer['tvec'] = [origtvec[i] for i in indices]
    else:
        indices = range(len(origtvec))
    
    for key in epititles.keys():
        percent = 100 if key in ['prev','force'] else 1 # Whether to multiple results by 100
        
        uncer[key] = dict()
        uncer[key]['pops'] = [dict() for p in xrange(D['G']['npops'])]
        uncer[key]['tot'] = dict()
        if key not in ['prev','force']: # For stacked area plots -- an option for everything except prevalence and force-of-infection
            uncer[key]['popstacked'] = dict()
            uncer[key]['popstacked']['pops'] = []
            uncer[key]['popstacked']['legend'] = []
            uncer[key]['popstacked']['title'] = epititles[key]
            uncer[key]['popstacked']['ylabel'] = epiylabels[key]
        for p in xrange(D['G']['npops']):
            uncer[key]['pops'][p]['best'] = (R[key]['pops'][0][p,:]*percent)[indices].tolist()
            uncer[key]['pops'][p]['low'] = (R[key]['pops'][1][p,:]*percent)[indices].tolist()
            uncer[key]['pops'][p]['high'] = (R[key]['pops'][2][p,:]*percent)[indices].tolist()
            uncer[key]['pops'][p]['title'] = epititles[key] + ' - ' + D['G']['meta']['pops']['short'][p]
            uncer[key]['pops'][p]['ylabel'] = epiylabels[key]
            if key not in ['prev','force']:
                uncer[key]['popstacked']['pops'].append(uncer[key]['pops'][p]['best'])
                uncer[key]['popstacked']['legend'].append(D['G']['meta']['pops']['short'][p])
        uncer[key]['tot']['best'] = (R[key]['tot'][0]*percent)[indices].tolist()
        uncer[key]['tot']['low'] = (R[key]['tot'][1]*percent)[indices].tolist()
        uncer[key]['tot']['high'] = (R[key]['tot'][2]*percent)[indices].tolist()
        uncer[key]['tot']['title'] = epititles[key] + ' - Overall'
        uncer[key]['tot']['ylabel'] = epiylabels[key]
        uncer[key]['xlabel'] = 'Years'
        
        if key=='prev':
            epidata = D['data']['key']['hivprev'][0] # TODO: include uncertainties
            uncer['prev']['ydata'] = zeros((D['G']['npops'],ndatayears)).tolist()
        if key=='plhiv':
            epidata = nan+zeros(ndatayears) # No data
            uncer['plhiv']['ydata'] = zeros(ndatayears).tolist()
        if key=='inci':
            epidata = D['data']['opt']['numinfect'][0]
            uncer['inci']['ydata'] = zeros(ndatayears).tolist()
        if key=='force':
            epidata = nan+zeros(ndatayears) # No data
            uncer['force']['ydata'] = zeros(ndatayears).tolist()
        if key=='death':
            epidata = D['data']['opt']['death'][0]
            uncer['death']['ydata'] = zeros(ndatayears).tolist()
        if key=='daly':
            epidata = nan+zeros(ndatayears) # No data
            uncer['daly']['ydata'] = zeros(ndatayears).tolist()
        if key=='dx':
            epidata = D['data']['opt']['numdiag'][0]
            uncer['dx']['ydata'] = zeros(ndatayears).tolist()
        if key=='tx1':
            epidata = D['data']['txrx']['numfirstline'][0]
            uncer['tx1']['ydata'] = zeros(ndatayears).tolist()
        if key=='tx2':
            epidata = D['data']['txrx']['numsecondline'][0]
            uncer['tx2']['ydata'] = zeros(ndatayears).tolist()


        if size(epidata,axis=0)==D['G']['npops']: # It's by population
            for p in xrange(D['G']['npops']):
                thispopdata = epidata[p]
                if len(thispopdata) == 1: 
                    thispopdata = nan+zeros(ndatayears) # If it's an assumption, just set with nans
                elif len(thispopdata) != ndatayears:
                    raise Exception('Expect data length of 1 or %i, actually %i' % (ndatayears, len(thispopdata)))
                uncer[key]['ydata'][p] = (asarray(thispopdata)*percent).tolist() # Stupid, but make sure it's an array, then make sure it's a list
        elif size(epidata[0])==1 and ndim(epidata)==1: # It's not by population
            uncer[key]['ydata'] = (array(epidata)*percent).tolist()
            if len(uncer[key]['ydata']) == 1:
                uncer[key]['ydata'] = nan+zeros(ndatayears) # If it's an assumption, just set with nans
            if len(uncer[key]['ydata']) != ndatayears:
                raise Exception('Expect data length of 1 or %i, actually %i' % (ndatayears, len(uncer[key]['ydata'])))
        else:
            raise Exception("Can't figure out size of epidata; doesn't seem to be a vector or a matrix")
    
    
    # Financial cost outputs
    for key in ['costann', 'costcum']:
        uncer[key] = dict()
        origkey = 'annual' if key=='costann' else 'cumulative'
        #Set up stacked storage
        uncer[key]['stacked'] = dict()
        if key == 'costcum':
            uncer[key]['stacked']['costs'] = []
            uncer[key]['stacked']['legend'] = []
            uncer[key]['stacked']['title'] = 'Cumulative HIV-related financial costs'
            uncer[key]['stacked']['ylabel'] = R['costshared'][origkey]['total']['ylabel']
        else:
            for yscale in ['total','gdp','revenue','govtexpend','totalhealth','domestichealth']:
                uncer[key]['stacked'][yscale] = dict()
                uncer[key]['stacked'][yscale]['costs'] = []
                uncer[key]['stacked'][yscale]['legend'] = []
                uncer[key]['stacked'][yscale]['title'] = 'Annual HIV-related financial costs'
                if 'ylinedata' in R['costshared'][origkey]['total'][yscale]:
                    uncer[key]['stacked'][yscale]['ylabel'] = R['costshared'][origkey]['total'][yscale]['ylabel']

        #Loop through cost types
        for ac in ['total']: #['total','future','existing']:
            uncer[key][ac] = dict()
            if key=='costcum':
                # Individual line graphs with uncertainty
                uncer[key][ac]['best'] = R[key][ac][0][indices].tolist()
                uncer[key][ac]['low'] = R[key][ac][1][indices].tolist()
                uncer[key][ac]['high'] = R[key][ac][2][indices].tolist()
                uncer[key][ac]['xdata'] = R['costshared'][origkey][ac]['xlinedata'][indices].tolist()
                uncer[key][ac]['title'] = R['costshared'][origkey][ac]['title']
                uncer[key][ac]['xlabel'] = R['costshared'][origkey][ac]['xlabel']
                uncer[key][ac]['ylabel'] = R['costshared'][origkey][ac]['ylabel']
                uncer[key][ac]['legend'] = ['Model']
                # Stacked graphs
                if ac != 'total':
                    uncer[key]['stacked']['costs'].append(uncer[key][ac]['best'])
                    uncer[key]['stacked']['legend'].append([ac['title']()])
            else:
                for yscale in ['total','gdp','revenue','govtexpend','totalhealth','domestichealth']:
                    uncer[key][ac][yscale] = dict()
                    if 'ylinedata' in R['costshared'][origkey][ac][yscale]:
                        # Individual line graphs with uncertainty
                        uncer[key][ac][yscale]['best'] = R[key][ac][yscale][0][indices].tolist()
                        uncer[key][ac][yscale]['low'] = R[key][ac][yscale][1][indices].tolist()
                        uncer[key][ac][yscale]['high'] = R[key][ac][yscale][2][indices].tolist()
                        uncer[key][ac][yscale]['xdata'] = R['costshared'][origkey][ac][yscale]['xlinedata'][indices].tolist()
                        uncer[key][ac][yscale]['title'] = R['costshared'][origkey][ac][yscale]['title']
                        uncer[key][ac][yscale]['xlabel'] = R['costshared'][origkey][ac][yscale]['xlabel']
                        uncer[key][ac][yscale]['ylabel'] = R['costshared'][origkey][ac][yscale]['ylabel']
                        uncer[key][ac][yscale]['legend'] = ['Model']
                        # Stacked graphs
                        if ac != 'total':
                            uncer[key]['stacked'][yscale]['costs'].append(uncer[key][ac][yscale]['best'])
                            uncer[key]['stacked'][yscale]['legend'].append([ac['title']()])
                            
    # Financial commitment outputs
    uncer['commit'] = dict()
    for yscale in ['total','gdp','revenue','govtexpend','totalhealth','domestichealth']:
        uncer['commit'][yscale] = dict()
        if 'ylinedata' in R['costshared']['annual']['total'][yscale]:
            # Individual line graphs with uncertainty
            uncer['commit'][yscale]['best'] = R['commit'][yscale][0][indices].tolist()
            uncer['commit'][yscale]['low'] = R['commit'][yscale][1][indices].tolist()
            uncer['commit'][yscale]['high'] = R['commit'][yscale][2][indices].tolist()
            uncer['commit'][yscale]['xdata'] = R['costshared']['commit'][yscale]['xlinedata'][indices].tolist()
            uncer['commit'][yscale]['title'] = R['costshared']['commit'][yscale]['title']
            uncer['commit'][yscale]['xlabel'] = R['costshared']['commit'][yscale]['xlabel']
            uncer['commit'][yscale]['ylabel'] = R['costshared']['commit'][yscale]['ylabel']
            uncer['commit'][yscale]['legend'] = ['Model']
    
    printv('...done gathering uncertainty results.', 4, verbose)
    return uncer




def gathermultidata(D, Rarr, annual=True, verbose=2, maxyear=2030):
    """ Gather multi-simulation results (scenarios and optimizations) into a form suitable for plotting. """
    from liboptima.utils import printv
    from copy import deepcopy
    printv('Gathering multi-simulation results...', 3, verbose)
    
    
    multi = dict()
    multi['nsims'] = len(Rarr) # Number of simulations
    multi['tvec'] = Rarr[0]['R']['tvec'].tolist() # Copy time vector
    multi['poplabels'] = D['G']['meta']['pops']['long']
    
    # Downsample to annual
    origtvec = deepcopy(multi['tvec'])
    if annual:
        dt = origtvec[1]-origtvec[0]
        allindices = range(0, len(origtvec), int(round(1/dt)))
        indices = []
        for i in allindices:
            if origtvec[i]<=maxyear:
                indices.append(i)
        multi['tvec'] = [origtvec[i] for i in indices]
        multi['tvec'] = [origtvec[i] for i in indices]
    else:
        indices = range(len(origtvec))
    
    for key in epititles.keys():
        percent = 100 if key in ['prev','force'] else 1 # Whether to multiple results by 100
        multi[key] = dict()
        multi[key]['pops'] = [dict() for p in xrange(D['G']['npops'])]
        for p in xrange(D['G']['npops']):
            multi[key]['pops'][p]['data'] = []
            multi[key]['pops'][p]['best'] = []
            multi[key]['pops'][p]['high'] = []
            multi[key]['pops'][p]['low'] = []
            multi[key]['pops'][p]['legend'] = []
            multi[key]['pops'][p]['title'] = epititles[key] + ' - ' + D['G']['meta']['pops']['short'][p]
            multi[key]['pops'][p]['ylabel'] = epiylabels[key]
            for sim in xrange(multi['nsims']):
                multi[key]['pops'][p]['data'].append((Rarr[sim]['R'][key]['pops'][0][p,:]*percent)[indices].tolist())
                multi[key]['pops'][p]['best'].append((Rarr[sim]['R'][key]['pops'][0][p,:]*percent)[indices].tolist())
                multi[key]['pops'][p]['low'].append((Rarr[sim]['R'][key]['pops'][1][p,:]*percent)[indices].tolist())
                multi[key]['pops'][p]['high'].append((Rarr[sim]['R'][key]['pops'][2][p,:]*percent)[indices].tolist())
                multi[key]['pops'][p]['legend'].append(Rarr[sim]['label'])
        multi[key]['tot'] = dict()
        multi[key]['tot']['data'] = []
        multi[key]['tot']['best'] = []
        multi[key]['tot']['low'] = []
        multi[key]['tot']['high'] = []
        multi[key]['tot']['legend'] = []
        multi[key]['tot']['title'] = epititles[key] + ' - Overall'
        multi[key]['tot']['ylabel'] = epiylabels[key]
        multi[key]['xlabel'] = 'Years'
        for sim in xrange(multi['nsims']):
            multi[key]['tot']['data'].append((Rarr[sim]['R'][key]['tot'][0]*percent)[indices].tolist())
            multi[key]['tot']['best'].append((Rarr[sim]['R'][key]['tot'][0]*percent)[indices].tolist())
            multi[key]['tot']['low'].append((Rarr[sim]['R'][key]['tot'][1]*percent)[indices].tolist())
            multi[key]['tot']['high'].append((Rarr[sim]['R'][key]['tot'][2]*percent)[indices].tolist())
            multi[key]['tot']['legend'].append(Rarr[sim]['label']) # Add legends
    
    # Financial cost outputs
    for key in ['costann', 'costcum']:
        multi[key] = dict()
        for ac in ['total']: #['total','future','existing']:
            origkey = 'annual' if key=='costann' else 'cumulative'
            multi[key][ac] = dict()
            if key=='costcum':
                multi[key][ac]['data'] = []
                multi[key][ac]['legend'] = []
                for sim in xrange(multi['nsims']):
                    thisdata = Rarr[sim]['R'][key][ac][0][indices].tolist()
                    multi[key][ac]['data'].append(thisdata)
                    multi[key][ac]['legend'].append(Rarr[sim]['label']) # Add legends
                    multi[key][ac]['xdata']  = Rarr[sim]['R']['costshared'][origkey][ac]['xlinedata'][indices].tolist()
                    multi[key][ac]['title']  = Rarr[sim]['R']['costshared'][origkey][ac]['title']
                    multi[key][ac]['xlabel'] = Rarr[sim]['R']['costshared'][origkey][ac]['xlabel']
                    multi[key][ac]['ylabel'] = Rarr[sim]['R']['costshared'][origkey][ac]['ylabel']
            else:
                for yscale in ['total','gdp','revenue','govtexpend','totalhealth','domestichealth']:
                    multi[key][ac][yscale] = dict()
                    multi[key][ac][yscale]['data'] = []
                    multi[key][ac][yscale]['legend'] = []
                    if 'ylinedata' in Rarr[sim]['R']['costshared'][origkey][ac][yscale]:
                        for sim in xrange(multi['nsims']):
                           thisdata = Rarr[sim]['R'][key][ac][yscale][0][indices].tolist()
                           multi[key][ac][yscale]['data'].append(thisdata)
                           multi[key][ac][yscale]['legend'].append(Rarr[sim]['label']) # Add legends
                           multi[key][ac][yscale]['xdata'] = Rarr[sim]['R']['costshared'][origkey][ac][yscale]['xlinedata'][indices].tolist()
                           multi[key][ac][yscale]['title'] = Rarr[sim]['R']['costshared'][origkey][ac][yscale]['title']
                           multi[key][ac][yscale]['xlabel'] = Rarr[sim]['R']['costshared'][origkey][ac][yscale]['xlabel']
                           multi[key][ac][yscale]['ylabel'] = Rarr[sim]['R']['costshared'][origkey][ac][yscale]['ylabel']                
        
    # Financial commitment outputs
    multi['commit'] = dict()
    for yscale in ['total','gdp','revenue','govtexpend','totalhealth','domestichealth']:
        multi['commit'][yscale] = dict()
        multi['commit'][yscale]['data'] = []
        multi['commit'][yscale]['legend'] = []
        if 'ylinedata' in Rarr[sim]['R']['costshared']['annual']['total'][yscale]:
            for sim in xrange(multi['nsims']):
                thisdata = Rarr[sim]['R']['commit'][yscale][0][indices].tolist()
                multi['commit'][yscale]['data'].append(thisdata)
                multi['commit'][yscale]['legend'].append(Rarr[sim]['label']) # Add legends
                multi['commit'][yscale]['xdata'] = Rarr[sim]['R']['costshared']['commit'][yscale]['xlinedata'][indices].tolist()
                multi['commit'][yscale]['title'] = Rarr[sim]['R']['costshared']['commit'][yscale]['title']
                multi['commit'][yscale]['xlabel'] = Rarr[sim]['R']['costshared']['commit'][yscale]['xlabel']
                multi['commit'][yscale]['ylabel'] = Rarr[sim]['R']['costshared']['commit'][yscale]['ylabel']                

        
    printv('...done gathering multi-simulation results.', 4, verbose)
    return multi





def gatheroptimdata(D, result, verbose=2):
    """ Return the data for plotting the optimization results. """
    from liboptima.utils import printv
    printv('Gathering optimization results...', 3, verbose)
    
    optim = dict() # These optimization results
    optim['kind'] = result['kind'] # Flag for the kind of optimization
    optim['multi'] = gathermultidata(D, result['Rarr'], verbose=2) # Calculate data for displaying standard epidemiological results
    if optim['kind'] in ['constant', 'timevarying', 'multiyear']:
        try:
            optim['outcome'] = dict() # Plot how the outcome improved with optimization
            optim['outcome']['ydata'] = result['fval'].tolist() # Vector of outcomes
            optim['outcome']['xdata'] = range(len(result['fval'].tolist())) # Vector of iterations
            optim['outcome']['ylabel'] = 'Outcome'
            optim['outcome']['xlabel'] = 'Iteration'
            rinit = result['fval'][0]
            rfin = result['fval'][-1]
            rreduc = 100*(1 - result['fval'][-1]/result['fval'][0])
            if result['fval'][0]>1:
                optim['outcome']['title'] = 'Outcome (initial: %0.0f, final: %0.0f, reduction: %0.0f%%)' % (rinit, rfin, rreduc)
            else:
                optim['outcome']['title'] = 'Outcome (initial: %0.3f, final: %0.3f, reduction: %0.0f%%)' % (rinit, rfin, rreduc)
        except:
            optim['outcome'] = dict() # Plot how the outcome improved with optimization
            optim['outcome']['ydata'] = [0] # Vector of outcomes
            optim['outcome']['xdata'] = [0] # Vector of iterations
            optim['outcome']['ylabel'] = 'Outcome'
            optim['outcome']['xlabel'] = 'Iteration'
            optim['outcome']['title'] = 'Outcome'
    if optim['kind']=='constant':
        optim['alloc'] = []
        titles = ['Original','Optimal']
        for i in xrange(2): # Original and optimal
            optim['alloc'].append(dict())
            optim['alloc'][i]['piedata'] = result['allocarr'][i][0].tolist() # A vector of allocations, length nprogs, for pie charts
            optim['alloc'][i]['radardata'] = dict() # Structure for storing radar plot data
            optim['alloc'][i]['radardata']['best'] = result['allocarr'][i][0].tolist() # 'Best' estimate: the thick line in the radar plot
            optim['alloc'][i]['radardata']['low']  = result['allocarr'][i][1].tolist() # 'Low' estimate: the 
            optim['alloc'][i]['radardata']['high'] = result['allocarr'][i][2].tolist()
            optim['alloc'][i]['title'] = titles[i] # Titles for pies or radar charts
            optim['alloc'][i]['legend'] = D['data']['meta']['progs']['short'] # Program names, length nprogs, for pie and radar
            optim['alloc'][i]['coverage'] = {}
            optim['alloc'][i]['coverage']['num'] = {}
            optim['alloc'][i]['coverage']['num']['best'] = result['covnumarr'][i][0].tolist() # A vector of coverage levels, length nprogs, for coverage table
            optim['alloc'][i]['coverage']['num']['low'] = result['covnumarr'][i][1].tolist() # A vector of coverage levels, length nprogs, for coverage table
            optim['alloc'][i]['coverage']['num']['high'] = result['covnumarr'][i][2].tolist() # A vector of coverage levels, length nprogs, for coverage table
            optim['alloc'][i]['coverage']['per'] = {}
            optim['alloc'][i]['coverage']['per']['best'] = result['covperarr'][i][0].tolist() # A vector of coverage levels, length nprogs, for coverage table
            optim['alloc'][i]['coverage']['per']['low'] = result['covperarr'][i][1].tolist() # A vector of coverage levels, length nprogs, for coverage table
            optim['alloc'][i]['coverage']['per']['high'] = result['covperarr'][i][2].tolist() # A vector of coverage levels, length nprogs, for coverage table
    if optim['kind']=='timevarying' or optim['kind']=='multiyear':
        optim['alloc'] = dict() # Allocation structure
        optim['alloc']['stackdata'] = [] # Empty list
        for p in xrange(D['G']['nprogs']): # Loop over programs
            optim['alloc']['stackdata'].append(result['alloc'][p].tolist()) # Allocation array, nprogs x npts, for stacked area plots
        optim['alloc']['xdata'] = result['xdata'].tolist() # Years
        optim['alloc']['xlabel'] = 'Year'
        optim['alloc']['ylabel'] = 'Spending'
        optim['alloc']['title'] = 'Optimal allocation'
        optim['alloc']['legend'] = D['data']['meta']['progs']['short'] # Program names, length nprogs
    if optim['kind']=='range':
        optim['alloc'] = dict() # Allocations structure
        optim['alloc']['bardata'] = []
        for b in xrange(len(result['allocarr'])): # Loop over budgets
            optim['alloc']['bardata'].append(result['allocarr'][b].tolist()) # A vector of allocations, length nprogs
        optim['alloc']['xdata'] = result['budgets'].tolist() # Vector of budgets
        optim['alloc']['xlabels'] = result['budgetlabels'] # Budget labels
        optim['alloc']['ylabel'] = 'Spend'
        optim['alloc']['title'] = 'Budget allocations'
        optim['alloc']['legend'] = D['data']['meta']['progs']['short'] # Program names, length nprogs
        optim['outcome'] = dict() # Dictionary with names and values
        optim['outcome']['bardata'] = result['fval'] # Vector of outcomes, length nbudgets
        optim['outcome']['xdata'] = result['budgets'].tolist() # Vector of budgets
        optim['outcome']['xlabels'] = result['budgetlabels'] # Budget labels
        optim['outcome']['ylabel'] = 'Outcome'
        optim['outcome']['title'] = 'Outcomes'

    printv('...done gathering optimization results.', 4, verbose)
    return optim