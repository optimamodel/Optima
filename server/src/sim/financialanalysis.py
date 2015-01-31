"""
Created on Sat Nov 29 17:40:34 2014

@author: robynstuart

Version: 2015jan27
"""
from numpy import linspace, arange, append
from setoptions import setoptions
from utils import sanitize, smoothinterp

def financialanalysis(D, postyear=2015, S=None, makeplot=False):
    '''
    Plot financial commitment graphs
    '''
    
    # Checking inputs... 
    if not(isinstance(S,dict)): S = D.S # If not supplied as input, copy from D
    postyear = float(postyear) # Make sure the year for turning off transmission is a float

    # Initialise output structure of plot data
    plotdata = {}

    # Different y axis scaling options
    costdisplays = ['total','gdp','revenue','govtexpend','totalhealth','domestichealth']

    # Initialise other internal storage structures
    people, hivcosts, artcosts = {}, {}, {}

    # Set up variables for time indexing
    datatvec = arange(D.G.datastart, D.G.dataend+D.opt.dt, D.opt.dt)
    ndatapts = len(datatvec)
    simtvec = S.tvec
    noptpts = len(simtvec)

    # Get most recent ART unit costs
    progname = 'ART'
    prognumber = D.data.meta.progs.short.index(progname)
    artunitcost = sanitize([D.data.costcov.cost[prognumber][j]/D.data.costcov.cov[prognumber][j] for j in range(len(D.data.costcov.cov[prognumber]))])[-1]

    # Run a simulation with the force of infection set to zero from postyear... 
    opt = setoptions(nsims=1, turnofftrans=postyear)
    from model import model
    S0 = model(D.G, D.M, D.F[0], opt, initstate=None)

    # Extract the number of PLHIV under the baseline sim and the zero transmission sim
    people['total'] = S.people[:,:,:]
    people['existing'] = S0.people[:,:,:]
    hivcosts['total'] = [0.0]*noptpts
    hivcosts['existing'] = [0.0]*noptpts
    
    # Interpolate costs & economic indicators
    for healthno, healthstate in enumerate(D.G.healthstates):

        # Remove NaNs from data
        socialcosts = sanitize(D.data.econ.social.past[healthno])
        othercosts = sanitize(D.data.econ.health.past[healthno])

        # Interpolating
        newx = linspace(0,1,ndatapts)
        origx = linspace(0,1,len(socialcosts))
        socialcosts = smoothinterp(newx, origx, socialcosts, smoothness=5)
        origx = linspace(0,1,len(othercosts))
        othercosts = smoothinterp(newx, origx, othercosts, smoothness=5)

        # Extrapolating... holding constant for now. #TODO use growth rates when they have been added to the excel sheet
        othercosts = append(othercosts,[othercosts[-1]]*(noptpts-ndatapts))
        socialcosts = append(socialcosts,[socialcosts[-1]]*(noptpts-ndatapts))
        costs = [(socialcosts[j] + othercosts[j]) for j in range(noptpts)]

        # Calculate annual non-treatment costs for all PLHIV under the baseline sim and the zero transmission sim
        coststotal = [people['total'][D.G[healthstate],:,j].sum(axis = (0,1))*costs[j] for j in range(noptpts)]
        costsexisting = [people['existing'][D.G[healthstate],:,j].sum(axis = (0,1))*costs[j] for j in range(noptpts)]
        
        hivcosts['total'] = [hivcosts['total'][j] + coststotal[j] for j in range(noptpts)]
        hivcosts['existing'] = [hivcosts['existing'][j] + costsexisting[j] for j in range(noptpts)]

    # Calculate annual treatment costs for PLHIV
    tx1total = people['total'][D.G.tx1[0]:D.G.fail[-1],:,:].sum(axis=(0,1))
    tx2total = people['total'][D.G.tx2[0]:D.G.tx2[-1],:,:].sum(axis=(0,1))
    onarttotal = [tx1total[j] + tx2total[j] for j in range(noptpts)]
    artcosts['total'] = [onarttotal[j]*artunitcost for j in range(noptpts)]
    
    # Calculate annual treatment costs for new PLHIV
    tx1existing = people['existing'][D.G.tx1[0]:D.G.fail[-1],:,:].sum(axis=(0,1))
    tx2existing = people['existing'][D.G.tx2[0]:D.G.tx2[-1],:,:].sum(axis=(0,1))
    onartexisting = [tx1existing[j] + tx2existing[j] for j in range(noptpts)]
    artcosts['existing'] = [onartexisting[j]*artunitcost for j in range(noptpts)]

    # Cumulative sum function (b/c can't find an inbuilt one)
    def accumu(lis):
        total = 0
        for x in lis:
            total += x
            yield total

    # Set y axis scale and set y axis to the right time period
    for plottype in ['annual','cumulative']:
        plotdata[plottype] = {}
        for plotsubtype in ['existing','total','future']:
            plotdata[plottype][plotsubtype] = {}
            if plottype=='annual':
                for yscalefactor in costdisplays:
                    plotdata[plottype][plotsubtype][yscalefactor] = {}
                    plotdata[plottype][plotsubtype][yscalefactor]['xlinedata'] = simtvec
                    plotdata[plottype][plotsubtype][yscalefactor]['xlabel'] = 'Year'
                    plotdata[plottype][plotsubtype][yscalefactor]['title'] = 'Annual HIV-related financial commitments - ' + plotsubtype + 'infections'
                    if yscalefactor=='total':                    
                        if not plotsubtype=='future': plotdata[plottype][plotsubtype][yscalefactor]['ylinedata'] = [(hivcosts[plotsubtype][j] + artcosts[plotsubtype][j]) for j in range(noptpts)]
                        plotdata[plottype][plotsubtype][yscalefactor]['ylabel'] = 'USD'
                    else:
                        yscale = sanitize(D.data.econ[yscalefactor].past)
                        if isinstance(yscale,int): continue #raise Exception('No data have been provided for this varaible, so we cannot display the costs as a proportion of this')
                        origx = linspace(0,1,len(yscale))
                        yscale = smoothinterp(newx, origx, yscale, smoothness=5)
                        yscale = append(yscale,[yscale[-1]]*(noptpts-ndatapts))

                        if not plotsubtype=='future': plotdata[plottype][plotsubtype][yscalefactor]['ylinedata'] = [(hivcosts[plotsubtype][j] + artcosts[plotsubtype][j])/yscale[j] for j in range(noptpts)] 
                        plotdata[plottype][plotsubtype][yscalefactor]['ylabel'] = 'Proportion of ' + yscalefactor
            else:
                plotdata[plottype][plotsubtype]['xlinedata'] = simtvec
                plotdata[plottype][plotsubtype]['xlabel'] = 'Year'
                plotdata[plottype][plotsubtype]['ylabel'] = 'USD'
                plotdata[plottype][plotsubtype]['title'] = 'Cumulative HIV-related financial commitments - ' + plotsubtype + 'infections'
                if not plotsubtype=='future': plotdata[plottype][plotsubtype]['ylinedata'] = list(accumu([hivcosts[plotsubtype][j] + artcosts[plotsubtype][j] for j in range(noptpts)]))

    plotdata['cumulative']['future']['ylinedata'] = [plotdata['cumulative']['total']['ylinedata'][j] - plotdata['cumulative']['existing']['ylinedata'][j] for j in range(noptpts)]
    for yscalefactor in costdisplays:
        if 'ylinedata' in plotdata['annual']['total'][yscalefactor].keys():
            plotdata['annual']['future'][yscalefactor]['ylinedata'] = [plotdata['annual']['total'][yscalefactor]['ylinedata'][j] - plotdata['annual']['existing'][yscalefactor]['ylinedata'][j] for j in range(noptpts)]


    return plotdata


#example
#plotdata = financialanalysis(D, postyear=2015, S=D.S, makeplot=1)
#from matplotlib.pylab import figure, plot, hold, xlabel, ylabel, title #we don't need it for the whole module in web context

#figure()
#hold(True)
#plot(plotdata['annual']['total']['domestichealth']['xlinedata'],plotdata['annual']['total']['domestichealth']['ylinedata'], lw = 2, c = 'b')
#plot(plotdata['annual']['existing']['domestichealth']['xlinedata'],plotdata['annual']['existing']['domestichealth']['ylinedata'], lw = 2, c = 'r')
#plot(plotdata['annual']['future']['domestichealth']['xlinedata'],plotdata['annual']['future']['domestichealth']['ylinedata'], lw = 2, c = 'k')
