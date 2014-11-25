def makefittedpars(G, opt, verbose=2):
    """
    Prepares model parameters to run the simulation.
    
    Version: 2014nov23 by cliffk
    """
    
    from printv import printv
    from matplotlib.pylab import array
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    printv('Making fitted parameters...', 1, verbose)
    
    # Initialize fitted parameters
    F = [struct()]*opt.nsims
    for s in range(opt.nsims):
        F[s].__doc__ = 'Fitted parameters for simulation %i: initial prevalence, force-of-infection, diagnoses, treatment' % s
        F[s].init = perturb(G.npops)
        F[s].force = perturb(G.npops)
        F[s].dx = array([perturb(), perturb(), (G.datastart+G.dataend)/2, 1])
        F[s].tx1 = array([perturb(), perturb(), (G.datastart+G.dataend)/2, 1])
        F[s].tx2 = array([perturb(), perturb(), (G.datastart+G.dataend)/2, 1])
    
    return F


def perturb(n=1, perturbation=0.5):
    """
    Define an array of numbers evenly perturbed with a mean of 1.
    """
    from matplotlib.pylab import rand
    output = 1 + 2*perturbation*(rand(n)-0.5)
    return output
