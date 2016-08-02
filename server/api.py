import json
import os
import sys
import logging
import redis

from flask import Flask, redirect, Blueprint, g, session, make_response, abort

from flask_restful import Api
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask_restful_swagger import swagger

app = Flask(__name__)
app.config.from_pyfile('config.py')

import matplotlib
matplotlib.use(app.config["MATPLOTLIB_BACKEND"])

if os.environ.get('OPTIMA_TEST_CFG'):
    app.config.from_envvar('OPTIMA_TEST_CFG')

from .webapp import dbconn
dbconn.db = SQLAlchemy(app)
dbconn.redis = redis.StrictRedis.from_url(app.config["REDIS_URL"])

from .webapp.dbmodels import UserDb

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(userid):
    try:
        user = UserDb.query.filter_by(id=userid).first()
    except Exception:
        user = None
    return user


@login_manager.request_loader
def load_user_from_request(request):  # pylint: disable=redefined-outer-name

    # try to login using the secret url arg
    secret = request.args.get('secret')
    if secret:
        user = UserDb.query.filter_by(password=secret, is_admin=True).first()
        if user:
            return user

    # finally, return None if both methods did not login the user
    return None


@login_manager.unauthorized_handler
def unauthorized_handler():
    abort(401)

from .webapp.utils import OptimaJSONEncoder
from .webapp import webhandlers

api_blueprint = Blueprint('api', __name__, static_folder='static')

api = swagger.docs(Api(api_blueprint), apiVersion='2.0')

api.add_resource(webhandlers.User, '/api/user')
api.add_resource(webhandlers.UserDetail, '/api/user/<uuid:user_id>')
api.add_resource(webhandlers.CurrentUser, '/api/user/current')
api.add_resource(webhandlers.UserLogin, '/api/user/login')
api.add_resource(webhandlers.UserLogout, '/api/user/logout')

api.add_resource(webhandlers.Projects, '/api/project')
api.add_resource(webhandlers.ProjectsAll, '/api/project/all')
api.add_resource(webhandlers.Project, '/api/project/<uuid:project_id>')
api.add_resource(webhandlers.ProjectCopy, '/api/project/<uuid:project_id>/copy')
api.add_resource(webhandlers.ProjectFromData, '/api/project/data')
api.add_resource(webhandlers.ProjectData, '/api/project/<uuid:project_id>/data')
api.add_resource(webhandlers.ProjectDataSpreadsheet, '/api/project/<uuid:project_id>/spreadsheet')
api.add_resource(webhandlers.ProjectEcon, '/api/project/<uuid:project_id>/economics')
api.add_resource(webhandlers.Portfolio, '/api/project/portfolio')

api.add_resource(webhandlers.Optimizations, '/api/project/<uuid:project_id>/optimizations')
api.add_resource(webhandlers.OptimizationCalculation, '/api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/results')
api.add_resource(webhandlers.OptimizationGraph, '/api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/graph')
api.add_resource(webhandlers.OptimizationUpload, '/api/project/<uuid:project_id>/optimization/<uuid:optimization_id>/upload')

api.add_resource(webhandlers.Scenarios, '/api/project/<uuid:project_id>/scenarios')
api.add_resource(webhandlers.ScenarioSimulationGraphs, '/api/project/<uuid:project_id>/scenarios/results')

api.add_resource(webhandlers.Progsets, '/api/project/<uuid:project_id>/progsets')
api.add_resource(webhandlers.Progset, '/api/project/<uuid:project_id>/progset/<uuid:progset_id>')
api.add_resource(webhandlers.ProgsetParameters,
     '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>/parameters/<uuid:parset_id>')
api.add_resource(webhandlers.ProgsetOutcomes, '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>/effects')
api.add_resource(webhandlers.ProgsetUploadDownload, '/api/project/<uuid:project_id>/progset/<uuid:progset_id>/data')

api.add_resource(webhandlers.DefaultPrograms, '/api/project/<uuid:project_id>/defaults')
api.add_resource(webhandlers.DefaultPopulations, '/api/project/populations')
api.add_resource(webhandlers.DefaultParameters, '/api/project/<project_id>/parameters')

api.add_resource(webhandlers.Program, '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>/program')
api.add_resource(webhandlers.ProgramPopSizes,
    '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>/program/<uuid:program_id>/parset/<uuid:parset_id>/popsizes')
api.add_resource(webhandlers.ProgramCostcovGraph,
    '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>/programs/<uuid:program_id>/costcoverage/graph')

api.add_resource(webhandlers.Parsets, '/api/project/<uuid:project_id>/parsets')
api.add_resource(webhandlers.ParsetRenameDelete, '/api/project/<uuid:project_id>/parsets/<uuid:parset_id>')
api.add_resource(webhandlers.ParsetCalibration, '/api/project/<uuid:project_id>/parsets/<uuid:parset_id>/calibration')
api.add_resource(webhandlers.ParsetAutofit, '/api/project/<uuid:project_id>/parsets/<uuid:parset_id>/automatic_calibration')
api.add_resource(webhandlers.ParsetUploadDownload, '/api/project/<uuid:project_id>/parsets/<uuid:parset_id>/data')
api.add_resource(webhandlers.ResultsExport, '/api/results/<uuid:result_id>')

app.register_blueprint(api_blueprint, url_prefix='')


@api.representation('application/json')
def output_json(data, code, headers=None):
    inner = json.dumps(data, cls=OptimaJSONEncoder)
    resp = make_response(inner, code)
    resp.headers.extend(headers or {})
    return resp


@api_blueprint.before_request
def before_request():
    from server.webapp.dbmodels import UserDb
    dbconn.db.engine.dispose()
    g.user = None
    if 'user_id' in session:
        g.user = UserDb.query.filter_by(id=session['user_id']).first()


@app.route('/')
def site():
    """ site - needed to correctly redirect to it from blueprints """
    return redirect('/')


@app.route('/api', methods=['GET'])
def root():
    """ API root, nothing interesting here """
    return 'Optima API v.1.0.0'


def init_db():
    print("Loading DB...")

    dbconn.db.engine.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    dbconn.db.create_all()

    # clear dangling tasks from the last session
    from .webapp.dbmodels import WorkLogDb

    work_logs = dbconn.db.session.query(WorkLogDb)
    print "> Deleting dangling work_logs", work_logs.count()
    for work_log in work_logs:
        work_log.cleanup()
    work_logs.delete()

    dbconn.db.session.commit()

def init_logger():
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    init_logger()
    init_db()
    app.run(threaded=True, debug=True, use_debugger=False)
else:
    init_logger()
    init_db()
