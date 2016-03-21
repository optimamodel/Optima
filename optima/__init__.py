# -*- coding: utf-8 -*-
"""
This file performs all necessary imports, so Optima can be used either as

from .optima import Project, Parameters [etc.] [preferred]
or
import optima as op
or
from .optima import *


Now, the legal part:

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


Version: 2016jan30 by cliffk
"""

optimalicense = '''
Optima HIV -- HIV optimization and analysis tool
Copyright (C) 2016 by the Optima Consortium
'''
print(optimalicense)




## Specify the version, for the purposes of figuring out which version was used to create a project
__version__ = 2.0

# Create an empty list to stored failed imports
_failed = [] 



#####################################################################################################################
### Load helper functions/modules
#####################################################################################################################

## General modules
from uuid import uuid4 as uuid
from datetime import datetime; today = datetime.today
from copy import deepcopy as dcp

## Optimization algorithm
from . import asd as _asd
from .asd import asd

## Interpolation
from . import pchip as _pchip
from .pchip import pchip, plotpchip

## Color definitions
from . import colortools # Load high-level module as well
from .colortools import alpinecolormap, bicolormap, gridcolormap, vectocolor

## Utilities
from . import utils # Load high-level module as well
from .utils import blank, checkmem, dataindex, defaultrepr, findinds, getdate, gitinfo, isnumber, loadobj, loads, objectid, objatt, objmeth, objrepr, odict, OptimaException, pd, perturb, printarr, printdata, printv, quantile, runcommand, sanitize, saveobj, saves, scaleratio, setdate, sigfig, smoothinterp, tic, toc, vec2obj


#####################################################################################################################
### Load Optima functions and classes
#####################################################################################################################

## Project settings
from . import settings as _settings # Inter-project definitions, e.g. health states
from .settings import Settings, convertlimits, gettvecdt

## Create a blank spreadsheet
try:
    from . import makespreadsheet as _makespreadsheet
    from .makespreadsheet import makespreadsheet, makeeconspreadsheet, default_datastart, default_dataend
except: _failed.append('makespreadsheet')

## Load a completed a spreadsheet
from . import loadspreadsheet as _loadspreadsheet
from .loadspreadsheet import loadspreadsheet

## Generate results -- odd location, I know!
from . import results as _results
from .results import Result, Resultset, Multiresultset, BOC, getresults

## Define the model parameters
from . import parameters as _parameters
from .parameters import Par, Timepar, Popsizepar, Constant, Parameterset, makepars, makesimpars, partable, loadpartable, applylimits # Parameter and Parameterset classes

## Define and run the model
from . import model as _model
from .model import model, runmodel

## Define the programs and cost functions
from . import programs as _programs 
from .programs import Program, Programset 

## Economics functions -- WARNING, not functional yet
from . import economics as _economics
from .economics import loadeconomics, loadeconomicsspreadsheet, makeecontimeseries, getartcosts 

## Automatic calibration and sensitivity
from . import calibration as _calibration
from .calibration import sensitivity, autofit 

## Scenario analyses
from . import scenarios as _scenarios 
from .scenarios import Parscen, Budgetscen, Coveragescen, Progscen, runscenarios, makescenarios, defaultscenarios, getparvalues 

## Optimization analyses
from . import optimization as _optimization
from .optimization import Optim, defaultobjectives, defaultconstraints, optimize

## Plotting functions
from . import plotting as _plotting 
from .plotting import getplotselections, makeplots


#####################################################################################################################
### Want to add more modules to Optima? Do that above this line (unless they're non-essential plotting functions)
#####################################################################################################################



#####################################################################################################################
### Load optional plotting functions
#####################################################################################################################

## Load high level GUI module
try: from . import gui
except: _failed.append('gui')

## Load simple function for displaying results
try: from .gui import plotresults
except: _failed.append('plotresults')

## Handle the Python plotting
try: from .gui import pygui 
except: _failed.append('pygui')

## Handle the browser-based plotting
try: from .gui import browser 
except: _failed.append('browser')

# Do manual fitting
try: from .gui import manualfit 
except: _failed.append('manualfit')

# Plot all people
try: from .gui import plotpeople 
except: _failed.append('plotpeople')

# Plot all parameters
try: from .gui import plotpars 
except: _failed.append('plotpars')



#####################################################################################################################
### Finally, load high-level modules that depend on everything else
#####################################################################################################################

## Import the Project class that ties everything together
import project as _project
from .project import Project

# Portfolio class (container of Projects)
import portfolio as _portfolio
from .portfolio import Portfolio 


try:
    import geospatial as _geospatial
    from . import batchtools
    from .batchtools import batchautofit
    from .geospatial import geogui # Import GUI tools for geospatial analysis
except: 
    _failed.append('geospatial')

if not len(_failed): del _failed # If it's empty, don't bother keeping it



# Finally, load defaults
from . import defaults