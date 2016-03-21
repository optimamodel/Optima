import json
import flask.json
import optima as op
import numpy as np
from collections import OrderedDict
import math


def normalize_dict(elem):
    if isinstance(elem, list):
        return [normalize_dict(p) for p in elem]
    elif isinstance(elem, op.utils.odict):
        result = OrderedDict()
        for (k, v) in elem.iteritems():
            norm_k = str(k)
            if type(v) == op.utils.odict or isinstance(v, list):
                norm_v = normalize_dict(v)
            else:
                norm_v = v
            result[norm_k] = norm_v
        return result
    elif isinstance(elem, float):
        if math.isnan(elem):
            return None
    return elem


class OptimaJSONEncoder(flask.json.JSONEncoder):

    """
    Custom JSON encoder, supporting optima-specific objects.
    """

    def default(self, obj):
        """
        Support additional data types when encoding to JSON.
        """
#        print type(obj)
        if isinstance(obj, op.parameters.Parameterset):  # TODO preserve order of keys
            return OrderedDict([(k, normalize_dict(v)) for (k, v) in obj.__dict__.iteritems()])

        if isinstance(obj, op.parameters.Par):
            return OrderedDict([(k, normalize_dict(v)) for (k, v) in obj.__dict__.iteritems()])

        if isinstance(obj, np.float64):
            return float(obj)

        if isinstance(obj, np.ndarray):
            return [nan_to_null(p) for p in list(obj)]

        if isinstance(obj, np.bool_):
            return bool(obj)

        if isinstance(obj, set):
            return list(obj)

        if isinstance(obj, op.utils.odict):  # never seems to get there
            return normalize_dict(obj)

        if isinstance(obj, op.project.Project):
            return None

        if isinstance(obj, op.results.Resultset):
            return None

        return flask.json.JSONEncoder.default(self, obj)
