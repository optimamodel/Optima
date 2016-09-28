"""
webhandlers.py
==========

The webhandlers for project related API calls. This should only take functions
from dataio.py which refers to project ids, filenames, project names, and
JSON compatible summaries of PyOptima objects.

There should be no direct references to PyOptima objects, underlying file
structure or the database.
"""

import json
import os
import pprint

from flask import helpers, current_app, request, Response, make_response, flash, redirect, \
    url_for
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource
from flask.ext.restful_swagger import swagger
from server.webapp.dataio import create_user, parse_user_args, update_user, do_login_user, delete_user, \
    do_logout_current_user, report_exception_decorator, verify_admin_request_decorator

from . import dataio
from .dataio import load_project_summaries, create_project_with_spreadsheet_download, delete_projects, \
    load_project_summary, update_project_followed_by_template_data_spreadsheet, download_project, \
    update_project_from_prj, create_project_from_prj, copy_project, load_project_program_summaries, \
    load_project_parameters, load_zip_of_prj_files, load_data_spreadsheet_binary, load_template_data_spreadsheet, \
    update_project_from_data_spreadsheet, update_project_from_econ_spreadsheet, load_project_name, delete_econ, \
    load_parset_summaries, create_parset, copy_parset, delete_parset, rename_parset, load_parset_graphs, launch_autofit, \
    load_parameters, save_parameters, load_result_csv, load_result_mpld3_graphs, load_progset_summaries, create_progset, \
    save_progset, delete_progset, upload_progset, load_parameters_from_progset_parset, load_progset_outcome_summaries, \
    save_outcome_summaries, save_program, load_target_popsizes, load_costcov_graph, load_scenario_summaries, \
    save_scenario_summaries, make_scenarios_graphs, load_optimization_summaries, save_optimization_summaries, \
    upload_optimization_summary, launch_optimization, check_optimization, load_optimization_graphs, get_users, \
    create_project_from_spreadsheet
from .parse import get_default_populations
from .utils import get_post_data_json, get_upload_file


class ProjectsAll(Resource):
    method_decorators = [report_exception_decorator, verify_admin_request_decorator]

    @swagger.operation(summary="Returns list of project sumamaries (for admins)")
    def get(self):
        """
        GET /api/project/all
        """
        return {'projects': load_project_summaries()}


class Projects(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Returns list project summaries for current user")
    def get(self):
        """
        GET /api/project
        """
        return {'projects': load_project_summaries(current_user.id)}

    @swagger.operation(summary="Create new project")
    def post(self):
        """
        POST /api/project
        data-json: project_summary
        """
        project_summary = get_post_data_json()
        project_id, dirname, basename = create_project_with_spreadsheet_download(
            current_user.id, project_summary)
        response = helpers.send_from_directory(
            dirname,
            basename,
            as_attachment=True,
            attachment_filename=basename)
        response.status_code = 201
        response.headers['X-project-id'] = project_id
        return response

    @swagger.operation(summary="Bulk delete projects")
    def delete(self):
        """
        DELETE /api/project
        data-json: { projects: list of project_ids }
        """
        delete_projects(get_post_data_json()['projects'])
        return '', 204


class Project(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Returns a project summary')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>
        """
        return load_project_summary(project_id)

    @swagger.operation(summary='Update a project')
    def put(self, project_id):
        """
        PUT /api/project/<uuid:project_id>
        data-json: project_summary
        """
        project_summary = get_post_data_json()
        dirname, basename = update_project_followed_by_template_data_spreadsheet(
            project_id, project_summary)
        print("> Project template: %s" % basename)
        response = helpers.send_from_directory(
            dirname,
            basename,
            as_attachment=True,
            attachment_filename=basename)
        response.headers['X-project-id'] = project_id
        return response

    @swagger.operation(summary='Delete project')
    def delete(self, project_id):
        """
        DELETE /api/project/<uuid:project_id>
        """
        delete_projects([project_id])
        return '', 204


class ProjectData(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Download .prj file for project')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/data
        """
        print("> Download .prj for project %s" % project_id)
        dirname, filename = download_project(project_id)
        return helpers.send_from_directory(dirname, filename)

    @swagger.operation(summary='Update existing project with .prj')
    def post(self, project_id):
        """
        POST /api/project/<uuid:project_id>/data
        """
        uploaded_prj_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        update_project_from_prj(project_id, uploaded_prj_fname)
        reply = {
            'file': os.path.basename(uploaded_prj_fname),
            'result': 'Project %s is updated' % project_id,
        }
        return reply


class ProjectFromData(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Upload project with .prj/.xls')
    def post(self):
        """
        POST /api/project/data
        form:
            name: name of project
            xls: true
        file: upload
        """
        project_name = request.form.get('name')
        is_xls = request.form.get('xls', False)
        uploaded_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        if is_xls:
            project_id = create_project_from_spreadsheet(
                uploaded_fname, project_name, current_user.id)
        else:
            project_id = create_project_from_prj(
                uploaded_fname, project_name, current_user.id)
        response = {
            'file': os.path.basename(uploaded_fname),
            'name': project_name,
            'id': project_id
        }
        return response, 201


class ProjectCopy(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Copies project to a different name")
    def post(self, project_id):
        """
        POST /api/project/<uuid:project_id>/copy
        data-json:
            to: new project name
        """
        args = get_post_data_json()
        new_project_name = args['to']

        copy_project_id = copy_project(project_id, new_project_name)
        print("> Copied project %s -> %s" % (project_id, copy_project_id))

        payload = {
            'project': project_id,
            'copy_id': copy_project_id
        }
        return payload


class DefaultPrograms(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Returns default program summaries for program-set modal")
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/defaults
        """
        return {"programs": load_project_program_summaries(project_id)}


class DefaultParameters(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Returns default programs for program-set modal")
    def get(self, project_id):
        """
        GET /api/project/<project_id>/parameters
        """
        return {'parameters': load_project_parameters(project_id)}


class DefaultPopulations(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Returns default populations for project management')
    def get(self):
        """
        GET /api/project/populations
        """
        return {'populations': get_default_populations()}


class Portfolio(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Download projects as .zip')
    def post(self):
        """
        POST /api/project/portfolio
        data-json:
            projects: list of project ids
        """
        project_ids = get_post_data_json()['projects']
        print("> Portfolio requested for projects {}".format(project_ids))
        dirname, filename = load_zip_of_prj_files(project_ids)
        return helpers.send_from_directory(dirname, filename)


class ProjectDataSpreadsheet(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Downloads template/uploaded data spreadsheet')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/spreadsheet
        """
        fname, binary = load_data_spreadsheet_binary(project_id)
        if binary is not None:
            print("> Download previously-uploaded xls as %s" % fname)
            return Response(
                binary,
                mimetype='application/octet-stream',
                headers={
                    'Content-Disposition': 'attachment;filename=' + fname
                })
        else:
            dirname, basename = load_template_data_spreadsheet(project_id)
            print("> Template created: %s" % basename)
            return helpers.send_from_directory(dirname, basename, as_attachment=True)

    @swagger.operation(summary='Upload completed data spreadsheet')
    def post(self, project_id):
        """
        POST /api/project/<uuid:project_id>/spreadsheet
        file-upload
        """
        spreadsheet_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        update_project_from_data_spreadsheet(project_id, spreadsheet_fname)
        project_name = load_project_name(project_id)
        basename = os.path.basename(spreadsheet_fname)
        return '"%s" was successfully uploaded to project "%s"' % (basename, project_name)


class ProjectEcon(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Downloads template/uploaded econ spreadsheet')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/economics
        """
        fname, binary = load_econ_spreadsheet_binary(project_id)
        if binary is not None:
            print("> Download previously-uploaded xls as %s" % fname)
            return Response(
                binary,
                mimetype='application/octet-stream',
                headers={
                    'Content-Disposition': 'attachment;filename=' + fname
                })
        else:
            dirname, basename = load_template_econ_spreadsheet(project_id)
            print("> Template created: %s" % basename)
            return helpers.send_from_directory(dirname, basename, as_attachment=True)

    @swagger.operation(summary='Upload the economics data spreadsheet')
    def post(self, project_id):
        """
        POST /api/project/<uuid:project_id>/economics
        file-upload
        """
        econ_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        server_fname = update_project_from_econ_spreadsheet(project_id, econ_fname)
        reply = {
            'file': os.path.basename(server_fname),
            'success': 'Econ spreadsheet uploaded for project %s' % load_project_name(project_id),
        }
        return reply

    @swagger.operation(summary='Removes economics data from project')
    def delete(self, project_id):
        """
        DELETE /api/project/<uuid:project_id>/economics
        """
        delete_econ(project_id)


class Parsets(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(description='Returns a list of parset summaries')
    def get(self, project_id):
        """
        GET /api/project/<project_id>/parsets
        """
        print("> Load parsets")
        return {"parsets": load_parset_summaries(project_id)}

    @swagger.operation(description='Copy/create a parset, and returns a list of parset summaries')
    def post(self, project_id):
        """
        POST /api/project/<project_id>/parsets
        data-json:
            name: name of parset
            parset_id: id of parset (copy) or null (create
        """
        args = get_post_data_json()
        new_parset_name = args['name']
        parset_id = args.get('parset_id')

        if not parset_id:
            print("> Create parset " + new_parset_name)
            create_parset(project_id, new_parset_name)
        else:
            print("> Copy parset " + new_parset_name)
            copy_parset(project_id, parset_id, new_parset_name)

        return load_parset_summaries(project_id)


class ParsetRenameDelete(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(description='Delete parset with parset_id.')
    def delete(self, project_id, parset_id):
        """
        DELETE /api/project/<uuid:project_id>/parsets/<uuid:parset_id>
        """
        print("> Delete parset '%s'" % parset_id)
        delete_parset(project_id, parset_id)
        return '', 204

    @swagger.operation(description='Rename parset and returns a list of parset summaries')
    def put(self, project_id, parset_id):
        """
        PUT /api/project/<uuid:project_id>/parsets/<uuid:parset_id>
        """
        name = get_post_data_json()['name']
        print("> Rename parset '%s'" % name)
        rename_parset(project_id, parset_id, name)
        return load_parset_summaries(project_id)


class ParsetCalibration(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(description='Returns parameter summaries and graphs for a project/parset')
    def get(self, project_id, parset_id):
        """
        GET /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/calibration
        url-query:
            autofit: boolean - true loads the results from the autofit parameters
        """
        autofit = request.args.get('autofit', False)
        # calculation_type = 'autofit' if autofit else "calibration"
        # print "> Get calibration graphs for %s" % (calculation_type)
        return load_parset_graphs(project_id, parset_id, "calibration")

    @swagger.operation(description='Updates a parset and returns the graphs for a parset_id')
    def post(self, project_id, parset_id):
        """
        POST /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/calibration
        data-json:
            parameters: parset_summary
            which: list of graphs to generate
            autofit: boolean indicates to fetch the autofit version of the results
        """
        args = get_post_data_json()
        autofit = args.get('autofit', False)
        # calculation_type = 'autofit' if autofit else "calibration"
        parameters = args.get('parameters')
        which = args.get('which')
        # print "> Update calibration graphs for %s" % (calculation_type)
        return load_parset_graphs(
            project_id, parset_id, "calibration", which, parameters)


class ParsetAutofit(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Starts autofit task and returns calc_status')
    def post(self, project_id, parset_id):
        """
        POST: /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/automatic_calibration
        data-json:
            maxtime: int - number of seconds to run
        """
        maxtime = get_post_data_json().get('maxtime')
        return launch_autofit(project_id, parset_id, maxtime)

    @swagger.operation(summary='Returns the calc status for the current job')
    def get(self, project_id, parset_id):
        """
        GET: /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/automatic_calibration
        """
        from server.webapp.tasks import check_calculation_status
        print "> Checking calc state"
        calc_state = check_calculation_status(project_id, 'autofit-' + str(parset_id))
        pprint.pprint(calc_state, indent=2)
        if calc_state['status'] == 'error':
            raise Exception(calc_state['error_text'])
        return calc_state


class ParsetUploadDownload(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Return a JSON file of the parameters")
    def get(self, project_id, parset_id):
        """
        GET /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/data
        """
        print("> Download JSON file of parset %s" % parset_id)
        parameters = load_parameters(project_id, parset_id)
        response = make_response(json.dumps(parameters, indent=2))
        response.headers["Content-Disposition"] = "attachment; filename=parset.json"
        return response

    @swagger.operation(summary="Update from JSON file of the parameters")
    def post(self, project_id, parset_id):
        """
        POST /api/project/<uuid:project_id>/parsets/<uuid:parset_id>/data
        file-upload
        """
        par_json = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        print("> Upload parset JSON file '%s'" % par_json)
        parameters = json.load(open(par_json))
        save_parameters(project_id, parset_id, parameters)
        return load_parset_summaries(project_id)


class ResultsExport(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Returns result as downloadable .csv file")
    def get(self, result_id):
        """
        GET /api/results/<results_id>
        """
        load_dir, filename = load_result_csv(result_id)
        response = helpers.send_from_directory(load_dir, filename)
        response.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
        return response

    @swagger.operation(summary="Returns graphs of a result_id, using which selectors")
    def post(self, result_id):
        """
        POST /api/results/<results_id>
        data-json:
            result_id: uuid of results
        """
        args = get_post_data_json()
        return load_result_mpld3_graphs(result_id, args.get('which'))


class Progsets(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(description='Return progset summaries')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/progsets
        """
        return load_progset_summaries(project_id)

    @swagger.operation(description='Create a new progset')
    def post(self, project_id):
        """
        POST /api/project/<uuid:project_id>/progsets
        data-json: progset_summary
        """
        progset_summary = get_post_data_json()
        return create_progset(project_id, progset_summary)


class Progset(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(description='Update progset with the given id.')
    def put(self, project_id, progset_id):
        """
        PUT /api/project/<uuid:project_id>/progset/<uuid:progset_id>
        data-json: progset_summary
        """
        progset_summary = get_post_data_json()
        return save_progset(project_id, progset_id, progset_summary)

    @swagger.operation(description='Delete progset with the given id.')
    def delete(self, project_id, progset_id):
        """
        DELETE /api/project/<uuid:project_id>/progset/<uuid:progset_id>
        """
        delete_progset(project_id, progset_id)
        return '', 204


class ProgsetUploadDownload(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Update from JSON file of the parameters")
    def post(self, project_id, progset_id):
        """
        POST /api/project/<uuid:project_id>/progset/<uuid:progset_id>/data
        file-upload
        """
        json_fname = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        print("> Upload progset JSON file '%s'" % json_fname)
        progset_summary = json.load(open(json_fname))
        return upload_progset(project_id, progset_id, progset_summary)


class ProgsetParameters(Resource):

    @swagger.operation(description='Return parameters for progset outcome page')
    def get(self, project_id, progset_id, parset_id):
        """
        GET /api/project/<uuid:project_id>/progsets/<uuid:progset_id>/parameters/<uuid:parset_id>
        """
        return load_parameters_from_progset_parset(project_id, progset_id, parset_id)


class ProgsetOutcomes(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Returns list of outcomes for a progset')
    def get(self, project_id, progset_id):
        """
        GET /api/project/<uuid:project_id>/progsets/<uuid:progset_id>/effects
        """
        return load_progset_outcome_summaries(project_id, progset_id)

    @swagger.operation(summary='Saves the outcomes of a given progset, used in outcome page')
    def put(self, project_id, progset_id):
        """
        PUT /api/project/<uuid:project_id>/progsets/<uuid:progset_id>/effects
        """
        outcome_summaries = get_post_data_json()
        return save_outcome_summaries(project_id, progset_id, outcome_summaries)


class Program(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Saves a program summary to project')
    def post(self, project_id, progset_id):
        """
        POST /api/project/<uuid:project_id>/progsets/<uuid:progset_id>/program
        data-json: programs: program_summary
        """
        program_summary = get_post_data_json()['program']
        save_program(project_id, progset_id, program_summary)
        return 204


class ProgramPopSizes(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Return estimated popsize for a given program and parset')
    def get(self, project_id, progset_id, program_id, parset_id):
        """
        GET /api/project/{project_id}/progsets/{progset_id}/program/{program_id}/parset/{progset_id}/popsizes
        """
        payload = load_target_popsizes(project_id, parset_id, progset_id, program_id)
        return payload, 201


class ProgramCostcovGraph(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Returns an mpld3 dict that can be displayed with the mpld3 plugin')
    def get(self, project_id, progset_id, program_id):
        """
        GET /api/project/<uuid:project_id>/progsets/<uuid:progset_id>/programs/<uuid:program_id>/costcoverage/graph
        url-args:
            t: comma-separated list of years (>= startyear in data)
            parset_id: parset ID of project (not related to program targetpars)
            caption: string to display in graph
            xupperlim: maximum dollar shown
            perperson: cost per person shown as data point
        """
        args = request.args

        parset_id = args['parset_id']

        try:
            t = map(int, args['t'].split(','))
        except ValueError:
            t = None
        if t is None:
            return {}

        plotoptions = {}
        for x in ['caption', 'xupperlim', 'perperson']:
            if args.get(x):
                plotoptions[x] = args[x]

        print '>>>> Generating plot...'
        return load_costcov_graph(
            project_id, progset_id, program_id, parset_id, t, plotoptions)


class Scenarios(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='get scenarios for a project')
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/scenarios
        """
        return load_scenario_summaries(project_id)

    @swagger.operation(summary='update scenarios; returns scenarios so client-side can check')
    def put(self, project_id):
        """
        PUT /api/project/<uuid:project_id>/scenarios
        data-josn: scenarios: scenario_summaries
        """
        data = get_post_data_json()
        scenario_summaries = data['scenarios']
        return save_scenario_summaries(project_id, scenario_summaries)


class ScenarioSimulationGraphs(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Run scenarios and returns the graphs')
    def get(self, project_id):
        """
        GET /api/project/<project-id>/scenarios/results
        """
        return make_scenarios_graphs(project_id)


class Optimizations(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Returns list of optimization summaries")
    def get(self, project_id):
        """
        GET /api/project/<uuid:project_id>/optimizations
        """
        return load_optimization_summaries(project_id)

    @swagger.operation(summary="Uploads project with optimization summaries, and returns summaries")
    def post(self, project_id):
        """
        POST /api/project/<uuid:project_id>/optimizations
        data-json: optimization_summaries
        """
        optimization_summaries = get_post_data_json()
        return save_optimization_summaries(project_id, optimization_summaries)


class OptimizationUpload(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary="Uploads json of optimization summary")
    def post(self, project_id, optimization_id):
        """
        POST /api/project/<uuid:project_id>/optimization/<uuid:optimization_id>/upload
        data-json: optimization_summary
        """
        optim_json = get_upload_file(current_app.config['UPLOAD_FOLDER'])
        optim_summary = json.load(open(optim_json))
        return upload_optimization_summary(project_id, optimization_id, optim_summary)


class OptimizationCalculation(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(summary='Launch optimization calculation')
    def post(self, project_id, optimization_id):
        """
        POST /api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/results
        data-json: maxtime: time to run in int
        """
        maxtime = get_post_data_json().get('maxtime')
        return launch_optimization(project_id, optimization_id, int(maxtime)), 201

    @swagger.operation(summary='Poll optimization calculation for a project')
    def get(self, project_id, optimization_id):
        """
        GET /api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/results
        """
        return check_optimization(project_id, optimization_id)


class OptimizationGraph(Resource):
    method_decorators = [report_exception_decorator, login_required]

    @swagger.operation(description='Provides optimization graph for the given project')
    def post(self, project_id, optimization_id):
        """
        POST /api/project/<uuid:project_id>/optimizations/<uuid:optimization_id>/graph
        post-json: which: list of graphs to display
        """
        which = get_post_data_json().get('which')
        return load_optimization_graphs(project_id, optimization_id, which)


class User(Resource):

    method_decorators = [report_exception_decorator]

    @swagger.operation(summary='List users')
    @verify_admin_request_decorator
    def get(self):
        """
        GET /api/user
        """
        return {'users': get_users()}

    @swagger.operation(summary='Create a user')
    def post(self):
        """
        POST /api/user
        """
        args = parse_user_args(get_post_data_json())
        return create_user(args), 201


class UserDetail(Resource):

    method_decorators = [report_exception_decorator]

    @swagger.operation(summary='Delete a user')
    @verify_admin_request_decorator
    def delete(self, user_id):
        """
        DELETE /api/user/<uuid:user_id>
        """
        delete_user(user_id)
        return '', 204

    @swagger.operation(summary='Update a user')
    def put(self, user_id):
        """
        PUT /api/user/<uuid:user_id>
        """
        args = parse_user_args(get_post_data_json())
        return update_user(user_id, args)


class CurrentUser(Resource):
    method_decorators = [login_required, report_exception_decorator]

    @swagger.operation(summary='Return the current user')
    def get(self):
        return dataio.marshal_user(current_user)


class UserLogin(Resource):

    @swagger.operation(summary='Try to log a user in',)
    @report_exception_decorator
    def post(self):
        args = parse_user_args(get_post_data_json())
        return do_login_user(args)


class UserLogout(Resource):

    @swagger.operation(summary='Log the current user out')
    @report_exception_decorator
    def get(self):
        do_logout_current_user()
        flash(u'You have been signed out')
        return redirect(url_for("site"))