import os
from sim.dataio import DATADIR, loaddata, savedata
from flask import helpers

ALLOWED_EXTENSIONS=set(['txt','xlsx','xls'])

""" Finds out if this file is allowed to be uploaded """
def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def loaddir(app):
  loaddir = ''
  loaddir = app.config['UPLOAD_FOLDER']
  print("loaddir = %s" % loaddir)
  if not loaddir:
    loaddir = DATADIR
  return loaddir

def project_exists(folder, name):
  project_name = helpers.safe_join(folder, name+'.prj')
  print("project name: %s" % project_name)
  return os.path.exists(project_name)

"""
  loads the project with the given name from the given folder
  returns the model (D).
"""
def load_model(folder, name):
  project_file = helpers.safe_join(folder, name+'.prj')
  return loaddata(project_file)

def save_model(folder, name, model):
  project_file = helpers.safe_join(folder, name+'.prj')
  return savedata(project_file, model)
