import factory
import hashlib
import json

from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory

from server.webapp.dbmodels import ParsetsDb
from server.webapp.dbmodels import ProgramsDb
from server.webapp.dbmodels import ProjectDataDb
from server.webapp.dbmodels import ProjectDb, ProgsetsDb
from server.webapp.dbmodels import ResultsDb
from server.webapp.dbmodels import UserDb
from server.webapp.dbmodels import WorkLogDb
from server.webapp.dbmodels import WorkingProjectDb


class UserFactory(SQLAlchemyModelFactory):
    
    class Meta:
        model = UserDb

    name = 'test'
    email = Sequence(lambda n: 'user_{}@test.com'.format(n))
    password = hashlib.sha224("test").hexdigest()
    is_admin = False


class ProjectFactory(SQLAlchemyModelFactory):

    class Meta:
        model = ProjectDb

    name = factory.Faker('name')
    user_id = UserFactory().id
    datastart = 2000
    dataend = 2030
    populations = json.loads(
        [
            {
                "age_to": "49",
                "age_from": "15",
                "name": "People who inject drugs",
                "short_name": "PWID",
                "female": False,
                "male": False}
        ])
    version = '2.0'


class ParsetFactory(SQLAlchemyModelFactory):

    """
        Requires a project that can be generated by calling the
        ProjectFactory()
        example usage:
        project = ProjectFactory()
        ParsetFactory(project_id=parset.project_id)
    """
    class Meta:
        model = ParsetsDb

    project_id = factory.LazyAttribute(lambda n: n)
    name = factory.Faker('name')


class ResultFactory(SQLAlchemyModelFactory):

    """
        Requires a parset that can be generated by calling the ParsetFactory()
        example usage:
        parset = ParsetFactory()
        ResultFactory(parset_id=parset.id, project_id=parset.project_id)
    """
    class Meta:
        model = ResultsDb

    parset_id = factory.LazyAttribute(lambda n: n)
    project_id = factory.LazyAttribute(lambda n: n)
    calculation_type = 'simulation'


class WorkingProjectFactory(SQLAlchemyModelFactory):

    """
        Takes in an is_working attribute of Boolean type
        example usage:
        WorkingProjectFactory(is_working=True)
    """
    class Meta:
        model = WorkingProjectDb

    is_working = factory.LazyAttribute(lambda n: n)


class WorkLogFactory(SQLAlchemyModelFactory):

    class Meta:
        model = WorkLogDb

    project_id = ProjectFactory()


class ProjectDataFactory(SQLAlchemyModelFactory):

    """
        Requires a project that can be generated by calling the
        ProjectFactory()
        example usage:
        project = ProjectFactory()
        ProjectDataFactory(id=project.id)
    """
    class Meta:
        model = ProjectDataDb

    id - factory.LazyAttribute(lambda n: n)


class ProgsetsFactory(SQLAlchemyModelFactory):

    """
        Requires a project that can be generated by calling the
        ProjectFactory()
        example usage:
        project = ProjectFactory()
        ProgsetFactory(project_id=project.id)
    """
    class Meta:
        model = ProgsetsDb
    project_id = factory.LazyAttribute(lambda n: n)
    name = factory.Faker('name')


class ProgramsFactory(SQLAlchemyModelFactory):

    """
        Requires a project and a progsetthat can be generated by calling the
        ProjectFactory() and ProgsetFactory
        example usage:
        project = ProjectFactory()
        progset = ProgsetFactory(project_id=project.id)
        ProgramsFactory(progset_id=progset.id, project_id=project.id)
    """
    class Meta:
        model = ProgramsDb

    progset_id = factory.LazyAttribute(lambda n: n)
    project_id = factory.LazyAttribute(lambda n: n)
    category = 'test'
    name = factory.Faker('name')
    short_name = factory.Faker('name')
    active = True
