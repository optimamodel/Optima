# -*- coding: utf-8 -*-
"""
Created on Tue Aug 16 18:39:31 2016

@author: David Kedziora
"""

from optima import *
from geospatial import *

if __name__ == '__main__':
    makesheet(projectpath='blantyre-fresh.prj', spreadsheetpath='BlantyreSplitBlank.xlsx', copies=2, refyear=2017)
    makeproj(projectpath='blantyre-fresh.prj', spreadsheetpath='BlantyreSplitFilled.xlsx', destination='Regions')
    create(filepaths=['Regions/Blantyre - District 1.prj','Regions/Blantyre - District 2.prj'])
    addproj(filepaths=['balaka-fresh.prj'])   # Use addportfolio argument if not wanting to work with globals.
    saveport(filepath='blantyre-balaka.prt')    # Use portfolio argument if not wanting to work with globals.

    gaobjectives = defaultobjectives(verbose=0)
    gaobjectives['budget'] = 15000000.0 # Reset
    
    loadport(filepath='malawi-decent-two-state.prt')
    rungeo(objectives=gaobjectives, BOCtime=2)     # Use portfolio argument if not wanting to work with globals.
    export(filepath='malawi-decent-two-state-results.xlsx')
    plotgeo()