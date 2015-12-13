from server.webapp.fields import Uuid, Json, LargeBinary

from flask_restful import fields

project_data_fields = {
    'id': Uuid,
    'name': fields.String,
    'dataStart': fields.Integer,
    'dataEnd': fields.Integer,
    'populations': Json,
    'creation_time': fields.DateTime,
    'updated_time': fields.DateTime,
    'data_upload_time': fields.DateTime,
    'has_data': fields.Boolean
}

project_data_list_all_fields = {
    'id': Uuid,
    'name': fields.String,
    'dataStart': fields.Integer,
    'dataEnd': fields.Integer,
    'populations': Json,
    'creation_time': fields.DateTime,
    'updated_time': fields.DateTime,
    'data_upload_time': fields.DateTime,
    'user_id': Uuid
}

project_data_list_fields = {
    'id': Uuid,
    'name': fields.String,
    'dataStart': fields.Integer,
    'dataEnd': fields.Integer,
    'populations': Json,
    'creation_time': fields.DateTime,
    'updated_time': fields.DateTime,
    'data_upload_time': fields.DateTime
}

project_copy_fields = {
    'project': Uuid,
    'user': Uuid,
    'copy_id': Uuid
}

predefined_fields = {
    "programs": Json,
    "populations": Json,
    "categories": Json
}
