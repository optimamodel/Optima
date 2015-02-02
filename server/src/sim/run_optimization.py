"""
TEST_OPTIMIZATION

This function tests that the optimization is working.

Version: 2015jan31 by cliffk
"""

print('WELCOME TO OPTIMA')

testconstant = False
testmultibudget = False
testtimevarying = False
testmultiyear = False
testconstraints = True


## Set parameters
projectname = 'example'
verbose = 10
ntimepm = 2 # AS: Just use 1 or 2 parameters... using 3 or 4 can cause problems that I'm yet to investigate
maxiters = 1e3
maxtime = 60 # Don't run forever :)

if maxtime:
    from time import time
    starttime = time()
    def stoppingfunc():
        if time()-starttime>maxtime:
            return True
        else:
            return False
else:
    stoppingfunc = None



    

print('\n\n\n1. Making project...')
from makeproject import makeproject
D = makeproject(projectname=projectname, pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)

print('\n\n\n2. Updating data...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose, savetofile=False)


if testconstant:
    print('\n\n\n3. Running constant-budget optimization...')
    from optimize import optimize, defaultobjectives
    objectives = defaultobjectives(D, verbose=verbose)
    optimize(D, objectives=objectives, maxiters=maxiters, stoppingfunc=stoppingfunc, verbose=verbose)


if testtimevarying:
    print('\n\n\n4. Running constant-budget optimization...')
    from optimize import optimize, defaultobjectives
    objectives = defaultobjectives(D, verbose=verbose)
    objectives.timevarying = True
    optimize(D, objectives=objectives, maxiters=maxiters, stoppingfunc=stoppingfunc, verbose=verbose)


if testmultiyear:
    print('\n\n\n5. Running multi-year-budget optimization...')
    from optimize import optimize, defaultobjectives
    objectives = defaultobjectives(D, verbose=verbose)
    objectives.funding = 'variable'
    objectives.outcome.variable = [6e6, 5e6, 3e6, 4e6, 3e6, 6e6] # Variable budgets
    optimize(D, objectives=objectives, maxiters=maxiters, stoppingfunc=stoppingfunc, verbose=verbose)


if testmultibudget:
    print('\n\n\n6. Running multiple-budget optimization...')
    from optimize import optimize, defaultobjectives
    objectives = defaultobjectives(D, verbose=verbose)
    objectives.funding = 'range'
    objectives.outcome.budgetrange.minval = 0
    objectives.outcome.budgetrange.maxval = 1
    objectives.outcome.budgetrange.step = 0.5
    optimize(D, objectives=objectives, maxiters=maxiters, stoppingfunc=stoppingfunc, verbose=verbose)


if testconstraints:
    print('\n\n\n7. Running constrained constant-budget optimization...')
    from optimize import optimize, defaultobjectives, defaultconstraints
    objectives = defaultobjectives(D, verbose=verbose)
    constraints = defaultconstraints(D, verbose=verbose)
    constraintkeys = ['yeardecrease', 'yearincrease', 'totaldecrease', 'totalincrease']
    for key in constraintkeys:
        for p in range(D.G.nprogs):
            constraints[key][p].use = True # Turn on all constraints
    optimize(D, objectives=objectives, maxiters=maxiters, stoppingfunc=stoppingfunc, verbose=verbose)
    
print('\n\n\n8. Viewing optimization...')
from viewresults import viewmultiresults
viewmultiresults(D.plot.optim[-1].multi)



print('\n\n\nDONE.')