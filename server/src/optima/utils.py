import os
from sim.dataio import DATADIR
from flask import helpers, session


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


def upload_dir_user():
    from models import UserDb
    user = None
    if '_id' in session:
        user = UserDb.query.filter_by(id=session['user_id']).first()
        return os.path.join(DATADIR, str(user.id))
    return DATADIR

