"""
Plots cost-coverage, coverage-outcome and cost-outcome curves

Version: 2015jan19 by robynstuart
"""
from matplotlib.pylab import figure, plot, hold, xlabel, ylabel, title, xlim, ylim, gca, scatter
from matplotlib.ticker import MaxNLocator
from numpy import nan
from mpld3 import plugins
from utils import OptimaTickFormatter

# Set defaults for testing makeccocs
default_progname = 'PWID programs'
default_effect = {'paramtype':'sex', 'param':'condomreg', 'popname':u'Male PWID'}
default_ccparams = {'saturation': .7,
                    'coveragelower': .4,
                    'coverageupper':.5,
                    'funding':9e6,
                    'scaleup':.2,
                    'nonhivdalys':nan,
                    'xupperlim':2e7,
                    'cpibaseyear':nan,
                    'perperson':nan}
default_coparams = [0.15, 0.3, 0.4, 0.55]
default_arteligcutoff = 'gt350'
coverage_params = ['numost','numpmtct','numfirstline','numsecondline']

###############################################################################
from makeccocs import makecc, makeco, makecco
###############################################################################
def do_plotcc(plotdata_cc, figsize=None):
    """ Actually plot cost-coverage curve"""

    cost_coverage_figure = None
    if figsize:
        cost_coverage_figure = figure(figsize=figsize, dpi=100)
    else:
        cost_coverage_figure = figure()

    cost_coverage_figure.hold(True)

    axis = cost_coverage_figure.gca()

    if 'xlinedata' in plotdata_cc.keys():
        axis.plot(
            plotdata_cc['xlinedata'],
            plotdata_cc['ylinedata'][1],
            linestyle='--',
            linewidth=2,
            color='#000000')
        axis.plot(
            plotdata_cc['xlinedata'],
            plotdata_cc['ylinedata'][0],
            linestyle='-',
            linewidth=2,
            color='#a6cee3')
        axis.plot(
            plotdata_cc['xlinedata'],
            plotdata_cc['ylinedata'][2],
            linestyle='--',
            linewidth=2,
            color='#000000')
    axis.scatter(
        plotdata_cc['xscatterdata'],
        plotdata_cc['yscatterdata'],
        color='#666666')

    axis.set_xlim([plotdata_cc['xlowerlim'],plotdata_cc['xupperlim']])
    axis.set_ylim([plotdata_cc['ylowerlim'],plotdata_cc['yupperlim']])
    axis.tick_params(axis='both', which='major', labelsize=11)
    axis.set_xlabel(plotdata_cc['xlabel'], fontsize=11)
    axis.set_ylabel(plotdata_cc['ylabel'], fontsize=11)
    axis.get_xaxis().set_major_locator(MaxNLocator(nbins=3))
    axis.set_title(plotdata_cc['title'])

    # clear all plugins from the figure
    plugins.clear(cost_coverage_figure)
    plugins.connect(
        cost_coverage_figure,
        plugins.BoxZoom(button=False),
        plugins.Zoom(button=False),
        OptimaTickFormatter())

    return cost_coverage_figure


def plotcc(D, progname=default_progname, ccparams=default_ccparams, arteligcutoff=default_arteligcutoff):
    ''' Plot cost-coverage curve'''

    plotdata_cc, D = makecc(D, progname=progname, ccparams=ccparams, arteligcutoff=arteligcutoff)
    return do_plotcc(plotdata_cc)

###############################################################################
def do_plotco(plotdata_co, figsize = None):
    """ Actually Plot coverage-outcome curve"""
    coverage_outcome_figure = None
    if plotdata_co:
        if figsize:
            coverage_outcome_figure = figure(figsize = figsize, dpi=100)
        else:
            coverage_outcome_figure = figure()
        coverage_outcome_figure.hold(True)

        axis = coverage_outcome_figure.gca()

        if 'xlinedata' in plotdata_co.keys():
            axis.plot(
                plotdata_co['xlinedata'],
                plotdata_co['ylinedata'][0],
                linestyle='-',
                linewidth=2,
                color='#a6cee3')
            axis.plot(
                plotdata_co['xlinedata'],
                plotdata_co['ylinedata'][1],
                linestyle='--',
                linewidth=2,
                color='#000000')
            axis.plot(
                plotdata_co['xlinedata'],
                plotdata_co['ylinedata'][2],
                linestyle='--',
                linewidth=2,
                color='#000000')
        axis.scatter(
            plotdata_co['xscatterdata'],
            plotdata_co['yscatterdata'],
            color='#666666')

        axis.set_title(plotdata_co['title'])
        axis.tick_params(axis='both', which='major', labelsize=11)
        axis.set_xlabel(plotdata_co['xlabel'], fontsize=11)
        axis.set_ylabel(plotdata_co['ylabel'], fontsize=11)
        axis.get_xaxis().set_major_locator(MaxNLocator(nbins=3))
        axis.set_xlim([plotdata_co['xlowerlim'],plotdata_co['xupperlim']])
        axis.set_ylim([plotdata_co['ylowerlim'],plotdata_co['yupperlim']])

        # clear all plugins from the figure
        plugins.clear(coverage_outcome_figure)
        plugins.connect(
            coverage_outcome_figure,
            plugins.BoxZoom(button=False),
            plugins.Zoom(button=False),
            OptimaTickFormatter())

    return coverage_outcome_figure


def plotco(D, progname=default_progname, effect=default_effect, coparams=default_coparams, arteligcutoff=default_arteligcutoff):
    ''' Plot coverage-outcome curve'''

    plotdata_co, effect = makeco(D=D, progname=progname, effect=effect, coparams=coparams, arteligcutoff=arteligcutoff)
    return do_plotco(plotdata_co)

#################################################################################
def do_plotcco(plotdata_cco, figsize = None):
    """ Actually plot cost-outcome curve"""
    cost_outcome_figure = None
    if plotdata_cco:
        if figsize:
            cost_outcome_figure = figure(figsize = figsize, dpi=100)
        else:
            cost_outcome_figure = figure()
        cost_outcome_figure.hold(True)

        axis = cost_outcome_figure.gca()

        if 'xlinedata' in plotdata_cco.keys():
            axis.plot(
                plotdata_cco['xlinedata'],
                plotdata_cco['ylinedata'][0],
                linestyle='-',
                linewidth=2,
                color='#a6cee3')
            axis.plot(
                plotdata_cco['xlinedata'],
                plotdata_cco['ylinedata'][1],
                linestyle='--',
                linewidth=2,
                color='#000000')
            axis.plot(
                plotdata_cco['xlinedata'],
                plotdata_cco['ylinedata'][2],
                linestyle='--',
                linewidth=2,
                color='#000000')
        axis.scatter(
            plotdata_cco['xscatterdata'],
            plotdata_cco['yscatterdata'],
            color='#666666')

        axis.set_title(plotdata_cco['title'])
        axis.tick_params(axis='both', which='major', labelsize=11)
        axis.set_xlabel(plotdata_cco['xlabel'], fontsize=11)
        axis.set_ylabel(plotdata_cco['ylabel'], fontsize=11)
        axis.get_xaxis().set_major_locator(MaxNLocator(nbins=3))
        axis.set_xlim([plotdata_cco['xlowerlim'],plotdata_cco['xupperlim']])
        axis.set_ylim([plotdata_cco['ylowerlim'],plotdata_cco['yupperlim']])

        # clear all plugins from the figure
        plugins.clear(cost_outcome_figure)
        plugins.connect(
            cost_outcome_figure,
            plugins.BoxZoom(button=False),
            plugins.Zoom(button=False),
            OptimaTickFormatter())
    return cost_outcome_figure


def plotcco(D, progname=default_progname, effect=default_effect, ccparams=default_ccparams, coparams=default_coparams, \
    arteligcutoff=default_arteligcutoff):
    ''' Plot cost-outcome curve'''

    plotdata_cco, plotdata_co, effect = makecco(D, progname=progname, effect=effect, ccparams=ccparams, coparams=coparams, arteligcutoff=arteligcutoff)
    return do_plotcco(plotdata_cco)

#################################################################################
def plotprogramcurves(D, progname=default_progname, ccparams=default_ccparams, coparams=default_coparams, arteligcutoff=default_arteligcutoff):
    ''' Plot all curves for a particular program '''

    plotcc(D, progname=progname, ccparams=ccparams, arteligcutoff=arteligcutoff)
    prognumber = [p['name'] for p in D['programs']].index(progname) # get program number
    for effectnumber, effect in enumerate(D['programs'][prognumber]['effects']):
        plotco(D, progname=progname, effect=effect, coparams=coparams, arteligcutoff=arteligcutoff)
        plotcco(D, progname=progname, effect=effect, ccparams=ccparams, coparams=coparams, arteligcutoff=arteligcutoff)

#################################################################################
def plotall(D, ccparams = default_ccparams, coparams = default_coparams):
    for program in D['programs']:
        plotdata_cc, D = makecc(D=D, progname=program['name'])
        plotprogramcurves(D=D, progname=program['name'])
