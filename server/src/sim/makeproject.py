"""
MAKEPROJECT
http://54.200.79.218/#/project/create
Version: 2014oct29
"""

def makeproject(projectname='example', npops=6, nprogs=8, datastart=2000, dataend=2015, verbose=2):
    if verbose>=1: print('Making project...')
    
    from dataio import savedata
    from bunch import Bunch as struct
    projectfilename = projectname+'.prj'
    
    D = struct() # Data structure for saving everything
    D.__doc__ = 'Data structure for storing everything -- data, parameters, simulation results, velociraptors, etc.'
    D.G = struct() # "G" for "general parameters"
    D.G.__doc__ = 'General parameters for the model, including the number of population groups, project name, etc.'
    D.G.npops = npops
    D.G.nprogs = nprogs
    D.G.projectname = projectname
    D.G.datastart = datastart
    D.G.dataend = dataend
    savedata(projectfilename, D, verbose=verbose) # Create project -- #TODO: check if an existing project exists and don't overwrite it
    
    # Make an Excel template and then prompt the user to save it
    from makespreadsheet import makespreadsheet
    spreadsheetname = makespreadsheet(projectname, npops, nprogs, datastart, dataend, verbose=verbose)
    
    if verbose>=2: print('  ...done making project.')
    return spreadsheetname