## Imports and globals...need Qt since matplotlib doesn't support edit boxes, grr!
from optima import OptimaException, Settings, dcp, printv, sigfig, makeplots, getplotselections, gridcolormap, odict, isnumber, promotetolist, loadobj, checktype
from optima._plotting import sanitizeresults
from pylab import figure, close, floor, ion, ioff, isinteractive, axes, ceil, sqrt, array, show, pause
from pylab import subplot, ylabel, transpose, legend, fill_between, xlim, title, gcf
from matplotlib.widgets import CheckButtons, Button
from matplotlib.backends.backend_qt4agg import new_figure_manager_given_figure as nfmgf

global panel, results, origpars, tmppars, parset, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist, plotfig, panelfig, check, checkboxes, updatebutton, clearbutton, closebutton  # For manualfit GUI
if 1:  panel, results, origpars, tmppars, parset, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist, plotfig, panelfig, check, checkboxes, updatebutton, clearbutton, closebutton = [None]*17

##############################################################################
### USER-VISIBLE FUNCTIONS
##############################################################################


def plotresults(results, toplot=None, fig=None, **kwargs): # WARNING, should kwargs be for figure() or makeplots()???
    ''' 
    Does the hard work for updateplots() for pygui()
    Keyword arguments if supplied are passed on to figure().
    
    Usage:
        results = P.runsim('default')
        plotresults(results)
        
    Version: 1.3 (2016jan25) by cliffk
    '''
    
    if 'figsize' not in kwargs: kwargs['figsize'] = (14,10) # Default figure size
    if fig is None: fig = figure(facecolor=(1,1,1), **kwargs) # Create a figure based on supplied kwargs, if any
    
    # Do plotting
    wasinteractive = isinteractive() # You might think you can get rid of this...you can't!
    if wasinteractive: ioff()
    width,height = fig.get_size_inches()
    
    # Actually create plots
    plots = makeplots(results, toplot=toplot, die=True, figsize=(width, height))
    reanimateplots(plots) # Reconnect the plots to the matplotlib backend so they can be rendered
    nplots = len(plots)
    nrows = int(ceil(sqrt(nplots)))  # Calculate rows and columns of subplots
    ncols = nrows-1 if nrows*(nrows-1)>=nplots else nrows
    for p in range(len(plots)): 
        naxes = len(plots[p].axes)
        if naxes==1: # Usual situation: just plot the normal axis
            addplot(fig, plots[p].axes[0], name=plots.keys()[p], nrows=nrows, ncols=ncols, n=p+1)
        elif naxes>1: # Multiple axes, e.g. allocation bar plots -- have to do some maths to figure out where to put the plots
            origrow = floor(p/ncols)
            origcol = p%ncols # Column doesn't change
            newnrows = nrows*naxes
            newrowstart = naxes*origrow # e.g. 2 axes in 3rd row = 5th row in new system
            for a in range(naxes):
                thisrow = newrowstart+a # Increment rows
                newp = ncols*thisrow + origcol # Calculate new row/column
                addplot(fig, plots[p].axes[a], name=plots.keys()[p], nrows=int(newnrows), ncols=int(ncols), n=int(newp+1))
        else: pass # Must have 0 length or something
    
    if wasinteractive: ion()
    show()


def pygui(tmpresults, toplot=None, advanced=False, verbose=2, **kwargs):
    '''
    PYGUI
    
    Make a Python GUI for plotting results. Opens up a control window and a plotting window,
    and when "Update" is clicked, will clear the contents of the plotting window and replot.
    
    Usage:
        pygui(results, [toplot])
    
    where results is the output of e.g. runsim() and toplot is an optional list of form e.g.
        toplot = ['prev-tot', 'inci-pop']
    
    (see epiformatslist in plotting.py)
    
    Warning: the plots won't resize automatically if the figure is resized, but if you click
    "Update", then they will.    
    
    Version: 1.3 (2017feb07)
    '''
    
    global check, checkboxes, updatebutton, clearbutton, closebutton, panelfig, results
    results = sanitizeresults(tmpresults)
    
    ## Define options for selection
    plotselections = getplotselections(results, advanced=advanced)
    checkboxes = plotselections['keys']
    checkboxnames = plotselections['names']
    isselected = []
    toplot = promotetolist(toplot) # Ensure it's a list
    if toplot[0] is None or toplot[0]=='default': 
        toplot.pop(0) # Remove the first element
        defaultboxes = [checkboxes[i] for i,tf in enumerate(plotselections['defaults']) if tf] # WARNING, ugly -- back-convert defaults from true/false list to list of keys
        toplot.extend(defaultboxes)
    if len(toplot):
        tmptoplot = dcp(toplot) # Make a copy to compare arguments
        for key in checkboxes:
            if key in toplot:
                isselected.append(True)
                tmptoplot.remove(key)
            else:
                isselected.append(False)
        if len(tmptoplot)!=0:
            errormsg = 'Not all keys were recognized; mismatched ones were:\n'
            errormsg += '%s\n' % tmptoplot
            errormsg += 'Available keys are:\n'
            errormsg += '%s' % checkboxes
            if not advanced: errormsg += 'Set advanced=True for more options'
            printv(errormsg, 1, verbose=verbose)
    
    ## Set up control panel
    figwidth = 7
    figheight = 12
    fc = Settings().optimablue # Try loading global optimablue
    panelfig = figure(num='Optima control panel', figsize=(figwidth,figheight), facecolor=(0.95, 0.95, 0.95), **kwargs) # Open control panel
    checkboxaxes = axes([0.1, 0.07, 0.8, 0.9]) # Create checkbox locations
    updateaxes   = axes([0.1, 0.02, 0.2, 0.03]) # Create update button location
    clearaxes    = axes([0.4, 0.02, 0.2, 0.03]) # Create close button location
    closeaxes    = axes([0.7, 0.02, 0.2, 0.03]) # Create close button location
    check = CheckButtons(checkboxaxes, checkboxnames, isselected) # Actually create checkboxes
    
    # Reformat the checkboxes
    totstr = ' -- total' # analysis:ignore WARNING, these should not be explicit!!!!!
    stastr = ' -- stacked'
    perstr = ' -- population'
    nboxes = len(check.rectangles)
    for b in range(nboxes):
        label = check.labels[b]
        labeltext = label.get_text()
        labelpos = label.get_position()
        label.set_position((labelpos[0]*0.3,labelpos[1])) # Not sure why by default the check boxes are so far away
        if labeltext.endswith(perstr):    label.set_text('Per population') # Clear label
        elif labeltext.endswith(stastr):  label.set_text('Stacked') # Clear label
        else:                             label.set_weight('bold')
    
    updatebutton   = Button(updateaxes,   'Update', color=fc) # Make button pretty and blue
    clearbutton    = Button(clearaxes, 'Clear',  color=fc) # Make button pretty and blue
    closebutton    = Button(closeaxes,    'Close', color=fc) # Make button pretty and blue
    updatebutton.on_clicked(updateplots) # Update figure if button is clicked
    clearbutton.on_clicked(clearselections) # Clear all checkboxes
    closebutton.on_clicked(closegui) # Close figures
    updateplots(None) # Plot initially -- ACTUALLY GENERATES THE PLOTS




def manualfit(project=None, parsubset=None, name=-1, ind=0, maxrows=25, verbose=2, advanced=False, **kwargs):
    ''' 
    Create a GUI for doing manual fitting via the backend. Opens up three windows: 
    results, results selection, and edit boxes.
    
    parsubset can be a list of parameters the user can fit, e.g.
    parsubset=['initprev','force']
    
    maxrows is the number of rows (i.e. parameters) to display in each column.
    
    Note: to get advanced parameters and plots, set advanced=True.
    
    Version: 1.2 (2017feb10)
    '''
    
    # For edit boxes, we need this -- but import it here so only this function will fail
    from PyQt4 import QtGui
    
    ## Random housekeeping
    global panel, results, origpars, tmppars, parset, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist
    fig = figure(); close(fig) # Open and close figure...dumb, no? Otherwise get "QWidget: Must construct a QApplication before a QPaintDevice"
    ion() # We really need this here!
    nsigfigs = 4
    
    boxes = []
    texts = []
    
    ## Get the list of parameters that can be fitted
    parset = dcp(project.parsets[name])
    tmppars = parset.pars
    origpars = dcp(tmppars)
    
    mflists = parset.manualfitlists(parsubset=parsubset, advanced=advanced)
    fullkeylist    = mflists['keys']
    fullsubkeylist = mflists['subkeys']
    fulltypelist   = mflists['types']
    fullvallist    = mflists['values']
    fulllabellist  = mflists['labels']
    
    nfull = len(fulllabellist) # The total number of boxes needed
    results = project.runsim(name)
    pygui(results, **kwargs)
    
    
    
    def closewindows():
        ''' Close all three open windows '''
        closegui()
        panel.close()
    
    
    ## Define update step
    def manualupdate():
        ''' Update GUI with new results '''
        global results, tmppars, fullkeylist, fullsubkeylist, fulltypelist, fullvallist
        
        # Update parameter values from GUI values
        for b,box in enumerate(boxes): 
            fullvallist[b] = eval(str(box.text())) 
        
        # Create lists for update
        mflists = dict()
        mflists['keys'] = fullkeylist
        mflists['subkeys'] = fullsubkeylist
        mflists['types'] = fulltypelist
        mflists['values'] = fullvallist
        parset.update(mflists)
        
        # Rerun
        simparslist = parset.interp(start=project.settings.start, end=project.settings.end, dt=project.settings.dt)
        results = project.runsim(simpars=simparslist)
        updateplots(tmpresults=results, **kwargs)
        
    
    ## Keep the current parameters in the project; otherwise discard
    def keeppars():
        ''' Little function to reset origpars and update the project '''
        global origpars, tmppars, parset
        origpars = dcp(tmppars)
        parset.pars = tmppars
        project.parsets[name].pars = tmppars
        print('Parameters kept')
        return None
    
    
    def resetpars():
        ''' Reset the parameters to the last saved version -- WARNING, doesn't work '''
        global origpars, tmppars, parset
        tmppars = dcp(origpars)
        parset.pars = tmppars
        for i in range(nfull): boxes[i].setText(sigfig(fullvallist[i], sigfigs=nsigfigs))
        simparslist = parset.interp(start=project.settings.start, end=project.settings.end, dt=project.settings.dt)
        results = project.runsim(simpars=simparslist)
        updateplots(tmpresults=results)
        return None
    

    ## Set up GUI
    npars = len(fullkeylist)
    leftmargin = 10
    rowheight = 25
    colwidth = 450
    ncols = floor(npars/maxrows)+1
    nrows = ceil(nfull/float(ncols))
    panelwidth = colwidth*ncols
    panelheight = rowheight*(nfull/ncols+2)+50
    buttonheight = panelheight-rowheight*1.5
    boxoffset = 300+leftmargin
    
    panel = QtGui.QWidget() # Create panel widget
    panel.setGeometry(100, 100, panelwidth, panelheight)
    spottaken = [] # Store list of existing entries, to avoid duplicates
    for i in range(nfull):
        row = (i % nrows) + 1
        col = floor(i/float(nrows))
        spot = (row,col)
        if spot in spottaken: 
            errormsg = 'Cannot add a button to %s since there already is one!' % str(spot)
            raise OptimaException(errormsg)
        else: spottaken.append(spot)
        
        texts.append(QtGui.QLabel(parent=panel))
        texts[-1].setText(fulllabellist[i])
        texts[-1].move(leftmargin+colwidth*col, rowheight*row)
        
        boxes.append(QtGui.QLineEdit(parent = panel)) # Actually create the text edit box
        boxes[-1].move(boxoffset+colwidth*col, rowheight*row)
        printv('Setting up GUI checkboxes: %s' % [i, fulllabellist[i], boxoffset+colwidth*col, rowheight*row], 4, verbose)
        boxes[-1].setText(sigfig(fullvallist[i], sigfigs=nsigfigs))
        boxes[-1].returnPressed.connect(manualupdate)
    
    keepbutton  = QtGui.QPushButton('Keep', parent=panel)
    resetbutton = QtGui.QPushButton('Reset', parent=panel)
    closebutton = QtGui.QPushButton('Close', parent=panel)
    
    keepbutton.move(1*panelwidth/4, buttonheight)
    resetbutton.move(2*panelwidth/4, buttonheight)
    closebutton.move(3*panelwidth/4, buttonheight)
    
    keepbutton.clicked.connect(keeppars)
    resetbutton.clicked.connect(resetpars)
    closebutton.clicked.connect(closewindows)
    panel.show()





def plotpeople(project=None, people=None, tvec=None, ind=None, simind=None, start=2, end=None, pops=None, animate=False, skipempty=True, verbose=2, figsize=(16,10), **kwargs):
    '''
    A function to plot all people as a stacked plot
    
    "Exclude" excludes the first N health states -- useful for excluding susceptibles.
    
    Usage example:
        import optima as op
        P = op.defaults.defaultproject('simple')
        P.runsim()
        people = P.results[-1].raw[0]['people']
        op.gui.plotpeople(P, people)
        
    NB: for a multiresult, simind must not be None!
    
    Version: 2016feb04
    '''
    if pops is None: pops = Ellipsis # This is a slice
    elif isnumber(pops): pops = [pops]
    if pops is not Ellipsis: plottitle = str(array(project.parsets[0].popkeys)[array(pops)])
    else: plottitle = 'All populations'
    legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.02, 1), 'fontsize':11, 'title':''}
    nocolor = (0.9,0.9,0.9)
    labels = project.settings.statelabels
    
    if people is None:
        if ind is None: ind=-1
        try:
            people = project.results[ind].raw[0]['people'] # Try to get default people to plot
        except:
            if simind is None: simind = 1
            people = project.results[ind].raw[simind][0]['people'] # It's a multiresult: need another  index
        
    
    plotstyles = odict([
    ('susreg',   ('|','|')), 
    ('progcirc', ('+','|')), 
    ('undx',     ('O','o')), 
    ('dx',       ('.','o')), 
    ('care',     ('*','*')), 
    ('lost',     ('X','|')),
    ('usvl',     ('.','o')), 
    ('svl',      ('*','*')), 
    ])
    
    hatchstyles = []
    linestyles = []
    for key in plotstyles.keys():
        hatchstyles.extend([plotstyles[key][0] for lab in labels if lab.startswith(key)])
        linestyles.extend([plotstyles[key][1]  for lab in labels if lab.startswith(key)])
    
    labels = labels[start:end]
    hatchstyles = hatchstyles[start:end]
    linestyles = linestyles[start:end]
    
    ppl = people[start:end,:,:] # Exclude initial people
    ppl = ppl[:,pops,:] # Filter selected populations
    ppl = ppl[:,:,:].sum(axis=1) # Sum over people
    ppl = transpose(ppl) # So time is plotted on x-axis
    
    nstates = len(labels)
    colors = gridcolormap(nstates)
    if tvec is None:
        tvec = project.settings.maketvec() # WARNING, won't necessarily match this ppl, supply as argument if so
    bottom = 0*tvec
    figure(facecolor=(1,1,1), figsize=figsize, **kwargs)
    ax = subplot(111)
    ylabel('Number of people')
    title(plottitle)
    xlim((tvec[0], tvec[-1]))
    for st in range(nstates-1,-1,-1):
        this = ppl[:,st]
        if sum(this): 
            thiscolor = colors[st]
            haspeople = True
        else: 
            thiscolor = nocolor
            haspeople = False
        if haspeople or not skipempty:
            printv('State: %i/%i Hatch: %s Line: %s Color: %s' % (st, nstates, hatchstyles[st], linestyles[st], thiscolor), 4, verbose)
            fill_between(tvec, bottom, this+bottom, facecolor=thiscolor, alpha=1, lw=0, hatch=hatchstyles[st])
            bottom += this
        
            # Legend stuff
            ax.plot((0, 0), (0, 0), color=thiscolor, linewidth=10, label=labels[st], marker=linestyles[st]) # This loop is JUST for the legends! since fill_between doesn't count as a plot object, stupidly... -- WARNING, copied from plotepi()
            handles, legendlabels = ax.get_legend_handles_labels()
            legend(reversed(handles), reversed(legendlabels), **legendsettings)
            if animate:
                show()
                pause(0.001)
    
    return None
    


global plotparsbackbut, plotparsnextbut, plotparslider
def plotpars(parslist=None, start=None, end=None, verbose=2, rows=6, cols=5, figsize=(16,12), fontsize=8, die=True, **kwargs):
    '''
    A function to plot all parameters. 'pars' can be an odict or a list of pars odicts.
    
    Version: 2016jan30
    '''
    from optima import Par, makesimpars, tic, toc
    from numpy import array, vstack
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Button, Slider
    
    global position, plotparsbackbut, plotparsnextbut, plotparslider
    position = 0
    
    # In case the user tries to enter a project or parset -- WARNING, needs to be made more flexible!
    tmp = parslist
    try:  parslist = tmp.parsets[-1].pars # If it's a project
    except:
        try: parslist = tmp.pars # If it's a parset
        except: pass
    parslist = promotetolist(parslist) # Convert to list
    try:
        for i in range(len(parslist)): parslist[i] = parslist[i].pars
    except: pass # Assume it's in the correct form -- a list of pars odicts
    
    allplotdata = []
    for pars in parslist:
        count = 0
        simpars = makesimpars(pars, start=start, end=end)
        tvec = simpars['tvec']
        plotdata = array([['name','simpar','par_t', 'par_y']], dtype=object) # Set up array for holding plotting results
        for i,key1 in enumerate(pars):
            par = pars[key1]
            if isinstance(par, Par):
                if   hasattr(par,'y'): pardata = par.y # WARNING, add par.m as well?
                elif hasattr(par,'p'): pardata = par.p # Population size
                else: raise Exception('???')
                if hasattr(pardata, 'keys') and len(pardata.keys())>0: # Only ones that don't have a len are temp pars
                    nkeys = len(pardata.keys())
                    for k,key2 in enumerate(pardata.keys()):
                        if hasattr(par, 't'): t = par.t[key2]
                        else: t = tvec[0] # For a constant
                        count += 1
                        if nkeys==1: thissimpar = simpars[key1]
                        else: thissimpar = simpars[key1][k]
                        thisplot = array(['%3i. %s - %s' % (count-1, key1, key2), thissimpar, t, pardata[key2]], dtype=object)
                        if array(thissimpar).sum()==0: thisplot[0] += ' (zero)'
                        plotdata = vstack([plotdata, thisplot])
                else:
                    t = tvec[0] # For a constant
                    count += 1
                    thisplot = array(['%3i. %s' % (count-1, key1), simpars[key1], t, pardata], dtype=object)
                    plotdata = vstack([plotdata, thisplot])
        plotdata = plotdata[1:,:] # Remove header
        allplotdata.append(plotdata)
    
    
    ## Do plotting
    nplots = len(plotdata)
    if any([len(pltd)!=nplots for pltd in allplotdata]): 
        printv('Warning, not all pars are the same length, only plotting first', 2, verbose)
        allplotdata = allplotdata[0]
    nperscreen = rows*cols

    plotparsfig = plt.figure(facecolor=(0.9,0.9,0.9), figsize=figsize)
    plt.subplots_adjust(left=0.05, right=0.95, bottom=0.1, top=0.95, wspace=0.3, hspace=0.4)
    plotparsaxs = []
    count = 0
    for row in range(rows):
        for col in range(cols):
            count += 1
            plotparsaxs.append(plotparsfig.add_subplot(rows, cols, count))
    
    backframe = plotparsfig.add_axes([0.1, 0.03, 0.1, 0.03])
    sliderframe = plotparsfig.add_axes([0.3, 0.03, 0.4, 0.03])
    nextframe = plotparsfig.add_axes([0.8, 0.03, 0.1, 0.03])
    plotparsbackbut = Button(backframe, 'Back')
    plotparsnextbut = Button(nextframe, 'Next')
    plotparslider = Slider(sliderframe, '', 0, nplots, valinit=0, valfmt='%d')
    
    def updateb(event=None): 
        global position
        position -= nperscreen
        position = max(0,position)
        position = min(nplots-nperscreen, position)
        plotparslider.set_val(position)
    
    def updaten(event=None): 
        global position
        position += nperscreen
        position = max(0,position)
        position = min(nplots-nperscreen, position)
        plotparslider.set_val(position)
    
    def update(tmp=0):
        global position, plotparslider
        position = tmp
        position = max(0,position)
        position = min(nplots-nperscreen, position)
        t = tic()
        for i,ax in enumerate(plotparsaxs):
            ax.cla()
            for item in ax.get_xticklabels() + ax.get_yticklabels(): item.set_fontsize(fontsize)
            ax.hold(True)
            nplt = i+position
            if nplt<nplots:
                for pd,plotdata in enumerate(allplotdata):
                    try:
                        this = plotdata[nplt,:]
                        ax.set_title(this[0])
                        if   type(this[1])==odict:
                            if len(this[1].keys())==1:  this[1] = this[1][0]
                            elif len(this[1].keys())>1: raise OptimaException('Expecting a number or an array or even an odict with one key, but got an odict with multiple keys (%s)' % this[0])
                        if   isnumber(this[1]):        ax.plot(tvec, 0*tvec+this[1])
                        elif len(this[1])==0:          ax.set_title(this[0]+' is empty')
                        elif len(this[1])==1:          ax.plot(tvec, 0*tvec+this[1])
                        elif len(this[1])==len(tvec):  ax.plot(tvec, this[1])
                        else: pass # Population size, doesn't use control points
                        printv('Plot %i/%i...' % (i*len(allplotdata)+pd+1, len(plotparsaxs)*len(allplotdata)), 2, verbose)
                    except Exception as E: 
                        if die: raise E
                        else: print('??????: %s' % E.message)
                    try: 
                        if not(hasattr(this[3],'__len__') and len(this[3])==0): ax.scatter(this[2],this[3])
                    except Exception: pass # print('Problem with "%s": "%s"' % (this[0], E.message))
                    if pd==len(allplotdata)-1: # Do this for the last plot only
                        ax.set_ylim((0,1.1*ax.get_ylim()[1]))
                        ax.set_xlim((tvec[0],tvec[-1]))
        toc(t)
                
    update()
    plotparsbackbut.on_clicked(updateb)
    plotparsnextbut.on_clicked(updaten)
    plotparslider.on_changed(update)
    return allplotdata


def loadplot(filename=None):
    '''
    Load a plot from a file and reanimate it.
    
    Example usage:
        import optima as op
        P = op.demo(0)
        op.saveplots(P, toplot='cascade', filetype='fig')
    
    Later:
        cascadefig = op.loadplot('cascade.fig')
    '''
    fig = loadobj(filename)
    reanimateplots(fig)
    return fig



##############################################################################
### HELPER FUNCTIONS
##############################################################################

def addplot(thisfig, thisplot, name=None, nrows=1, ncols=1, n=1):
    ''' Add a plot to an existing figure '''
    thisfig._axstack.add(thisfig._make_key(thisplot), thisplot) # Add a plot to the axis stack
    thisplot.change_geometry(nrows, ncols, n) # Change geometry to be correct
    orig = thisplot.get_position() # get the original position 
    widthfactor = 0.9/ncols**(1/4.)
    heightfactor = 0.9/nrows**(1/4.)
    pos2 = [orig.x0, orig.y0,  orig.width*widthfactor, orig.height*heightfactor] 
    thisplot.set_position(pos2) # set a new position
    thisplot.figure = thisfig # WARNING, none of these things actually help with the problem that the axes don't resize with the figure, but they don't hurt...
    thisplot.pchanged()
    thisplot.stale = True
    return None


def reanimateplots(plots=None):
    ''' Reconnect plots (actually figures) to the Matplotlib backend. plots must be an odict of figure objects. '''
    fignum = gcf().number # This is the number of the current active figure
    if not checktype(plots, odict): plots = odict({'Plot':plots}) # Convert to an odict
    for plt in plots.values(): nfmgf(fignum, plt) # Make sure each figure object is associated with the figure manager
    return None


def closegui(event=None):
    ''' Close all GUI windows '''
    global check, checkboxes, updatebutton, clearbutton, closebutton, panelfig, results
    try: close(plotfig)
    except: pass
    try: close(panelfig)
    except: pass
    return None


def getchecked(check=None):
    ''' Return a list of whether or not each check box is checked or not '''
    ischecked = []
    for box in range(len(check.lines)): ischecked.append(check.lines[box][0].get_visible()) # Stupid way of figuring out if a box is ticked or not
    return ischecked


def clearselections(event=None):
    global plotfig, check, checkboxes, results
    for box in range(len(check.lines)):
        for i in [0,1]: check.lines[box][i].set_visible(False)
    updateplots()
    return None
    
    
def updateplots(event=None, tmpresults=None, **kwargs):
    ''' Close current window if it exists and open a new one based on user selections '''
    global plotfig, check, checkboxes, results
    if tmpresults is not None: results = tmpresults
    
    # If figure exists, get size, then close it
    try: width,height = plotfig.get_size_inches(); close(plotfig) # Get current figure dimensions
    except: width,height = 14,12 # No figure: use defaults
    
    # Get user selections
    ischecked = getchecked(check)
    toplot = array(checkboxes)[array(ischecked)].tolist() # Use logical indexing to get names to plot
    
    # Do plotting
    if sum(ischecked): # Don't do anything if no plots
        plotfig = figure('Optima results', figsize=(width, height), facecolor=(1,1,1)) # Create figure with correct number of plots
        for key in ['toplot','fig','figsize']: kwargs.pop(key, None) # Remove duplicated arguments if they exist
        plotresults(results, toplot=toplot, fig=plotfig, figsize=(width, height), **kwargs)
    
    return None

