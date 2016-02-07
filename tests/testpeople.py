"""
Test to see if the calculation of people has changed.

Version: 2016feb06
"""

from numpy import shape, array
import optima as op
import os


refresh = 0 # Creates defaultpeople.ppl rather than copares
eps = 1e-3 # Don't expect a totally exact match
filename = 'defaultraw.npy'

P = op.defaults.defaultproject('generalized')
newraw = P.results[0].raw[0]

if refresh or not(os.path.exists(filename)):
    op.saveobj(filename, newraw)
    print('Created new "%s".' % filename)
else:
    oldraw = op.loadobj(filename)
    for key in ['people'] + oldraw.keys(): # Do all keys, but make sure people is first
        if type(oldraw[key])==type(array([])):
            diffraw = newraw[key]-oldraw[key]
            if (diffraw>eps).any(): # If not every element is a real number >0, throw an error
                if key!='people':
                    errormsg = 'WARNING, key "%s" does not match! Total mismatch: %s' % (key, sum(abs(diffraw)))
                    raise Exception(errormsg)
                if key=='people':
                    for t in range(shape(diffraw)[2]): # Loop over all heath states
                        for errstate in range(shape(diffraw)[0]): # Loop over all heath states
                            for errpop in range(shape(diffraw)[1]): # Loop over all populations
                                if diffraw[errstate,errpop,t]!=0:
                                    errormsg = 'WARNING, people do not match!\npeople[%i, %i, %i] = %f vs. %f' % (errstate, errpop, t, oldraw['people'][errstate,errpop,t], newraw['people'][errstate,errpop,t])
                                    raise Exception(errormsg)
    else:
        print('People are the same, yay! (max diff in people: %s)' % abs(newraw['people']-oldraw['people']).max())