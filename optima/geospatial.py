"""
GEOSPATIAL

This file defines everything needed for the Python GUI for geospatial analysis.

Version: 2016jan23
"""

from optima import Project, Portfolio, loadobj, defaultobjectives
from PyQt4 import QtGui
from pylab import figure, close
global geoguiwindow
geoguiwindow = None

def geogui():
    '''
    Open the GUI for doing geospatial analysis.
    
    Version: 2016jan23
    '''
    global geoguiwindow, portfolio, projectslist, objectives
    portfolio = None
    projectslist = []
    objectives = defaultobjectives()
    
    ## Set parameters
    wid = 300.0
    hei = 400.0
    top = 20
    spacing = 40
    left = 20.
    right = wid*2/3.
    extension = '.prj'
    
    ## Housekeeping
    fig = figure(); close(fig) # Open and close figure...dumb, no? Otherwise get "QWidget: Must construct a QApplication before a QPaintDevice"
    geoguiwindow = QtGui.QWidget() # Create panel widget
    geoguiwindow.setGeometry(100, 100, wid, hei)
    geoguiwindow.setWindowTitle('Optima geospatial analysis')
    projectslist = []
    
    ## Define buttons
    makesheetbutton = QtGui.QPushButton('1. Make geospatial template from project', parent=geoguiwindow)
    makeprojbutton  = QtGui.QPushButton('2. Auto-generate projects template', parent=geoguiwindow)
    createbutton    = QtGui.QPushButton('3a. Create portfolio from projects', parent=geoguiwindow)
    loadbutton      = QtGui.QPushButton('3b. Load existing portfolio', parent=geoguiwindow)
    rungeobutton    = QtGui.QPushButton('4. Run geospatial analysis', parent=geoguiwindow)
    exportbutton    = QtGui.QPushButton('5. Export results', parent=geoguiwindow)
    closebutton     = QtGui.QPushButton('Close', parent=geoguiwindow)
    
    allbuttons = [makesheetbutton, makeprojbutton, createbutton, loadbutton, rungeobutton, exportbutton, closebutton]
    
    ## Define other objects
    projectsbox = QtGui.QTextEdit(parent=geoguiwindow)
    
    ## Set button locations
    for b,button in enumerate(allbuttons):
        button.move(left, top+spacing*b)
#    makesheetbutton.move(left, top+spacing*0)
#    makeprojbutton.move(left, top+spacing*1)
#    makeprojbutton.move(left, top+spacing*1)
#    loadbutton.move(left, top+spacing*2)
#    rungeobutton.move(left, top+spacing*3)
#    exportbutton.move(left, hei-spacing)
#    closebutton.move(right, hei-spacing)
    
    ## Set other locations
    projectsbox.move(200, 200)
#    geoguiwindow.setCentralWidget(projectsbox)
    
    def loadprojects():
        global projectslist
        projectslist = []
        projectpaths = []
        filepaths = QtGui.QFileDialog.getOpenFileNames(caption='Choose project files/portfolio folder', filter='*'+extension)
        for filepath in filepaths:
            tmpproj = None
            try: tmpproj = loadobj(filepath, verbose=0)
            except: print('Could not load file "%s"; moving on...' % filepath)
            if tmpproj is not None: 
                try: 
                    assert type(tmpproj)==Project
                    projectslist.append(tmpproj)
                    projectpaths.append(filepath)
                    print('Project file "%s" loaded' % filepath)
                except: print('File "%s" is not an Optima project file; moving on...' % filepath)
        projectsbox.setText('\n'.join(projectpaths))
        portfolio = Portfolio()
        for project in projectslist: portfolio.addproject(project)
        return None
    
    ## Define functions
#    makesheetbutton.clicked.connect()
#    genprojbutton.clicked.connect()
    loadbutton.clicked.connect(loadprojects)
#    rungeobutton.clicked.connect()
#    exportbutton.clicked.connect()
    closebutton.clicked.connect(geoguiwindow.close)
    
    
#    keepbutton.move(0+buttonoffset, buttonheight)
#    resetbutton.move(200+buttonoffset, buttonheight)
#    closebutton.move(400+buttonoffset, buttonheight)
#    
#    keepbutton.clicked.connect(keeppars)
#    resetbutton.clicked.connect(resetpars)
#    closebutton.clicked.connect(closewindows)
    geoguiwindow.show()