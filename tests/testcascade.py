"""
Test the cascade

Version: 2016jan23 by cliffk
"""



## Define tests to run here!!!
tests = [
'compare',
]


##############################################################################
## Initialization -- same for every test script
##############################################################################

from optima import tic, toc, blank, pd # analysis:ignore

if 'doplot' not in locals(): doplot = True

def done(t=0):
    print('Done.')
    toc(t)
    blank()

blank()
print('Running tests:')
for i,test in enumerate(tests): print(('%i.  '+test) % (i+1))
blank()

T = tic()


##############################################################################
## The tests
##############################################################################





#####################################################################################################
if 'compare' in tests:
    t = tic()
    print('Running comparison test...')
    
    from optima import Project
    P = Project(spreadsheet='test7pops.xlsx')
    P.settings.usecascade = False
    pp = tic()
    P.runsim()
    toc(pp, label='model run without cascade')
    
    Q = Project(spreadsheet='test7pops.xlsx')
    Q.settings.usecascade = True
    qq = tic()
    Q.runsim()
    toc(qq, label='model run with cascade')
    
    
    
    if doplot:
        from optima import plotresults
        plotresults(P.results[-1], toplot=['prev-tot', 'numinci-sta'], figsize=(16,10), num='No cascade')
        plotresults(Q.results[-1], toplot=['prev-tot', 'numinci-sta'], figsize=(16,10), num='With cascade')
    
    done(t)






print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)