"""
DATAIO

Data input/output. Uses JSON format.

Version: 2014nov17 by cliffk
"""

import os


TEMPLATEDIR = "/tmp/templates"
PROJECTDIR = "/tmp/projects"

def fullpath(filename, datadir=None):
    """
    "Normalizes" filename:  if it is full path, leaves it alone. Otherwise, prepends it with datadir.
    """

    if datadir == None:
        datadir = current_app.config['UPLOAD_FOLDER']

    result = filename

    # get user dir path
    datadir = upload_dir_user(datadir)

    if not(os.path.exists(datadir)):
        os.makedirs(datadir)
    if os.path.dirname(filename)=='' and not os.path.exists(filename):
        result = os.path.join(datadir, filename)

    return result

def templatepath(filename):
    return fullpath(filename, TEMPLATEDIR)

def projectpath(filename):
    return fullpath(filename, PROJECTDIR)

def savedata(filename, data, update=True, verbose=2):
    """
    Saves the pickled data into the file (either updates it or just overwrites).
    """
    print('Saving data...')

    from json import dump

    filename = projectpath(filename)

    wfid = open(filename,'wb')
    dump(tojson(data), wfid)
    wfid.close()
    print('..created new file')
    print(' ...done saving data at %s.' % filename)
    return filename


def loaddata(filename, verbose=2):
    """
    Loads the file and imports json data from it.
    If the file cannot be load as json, tries loading it with cPickle.
    """

    print('Loading data...')
    if not os.path.exists(filename):
        filename = projectpath(filename)

    import json
    rfid = open(filename,'rb')
    data = fromjson(json.load(rfid))
    rfid.close()
    print('...done loading data.')
    return data



def tojson(x):
    """ Convert an object to JSON-serializable format, handling e.g. Numpy arrays """
    # For numpy arrays - identified by np_array and then np_dtype as a secondary key
    # For numpy float64 - identified by np_float64 only
    from numpy import ndarray, isnan, float64

    if isinstance(x, dict):
        return dict( (k, tojson(v)) for k,v in x.iteritems() )
    elif isinstance(x, (list, tuple)):
        return type(x)( tojson(v) for v in x )
    elif isinstance(x, ndarray):
        return {"np_array":[tojson(v) for v in x.tolist()], "np_dtype":x.dtype.name}
    elif isinstance(x,float64):
        return {"np_float64":x}
    elif isinstance(x, float) and isnan(x):
        return None
    else:
        return x


def fromjson(x):
    """ Convert an object from JSON-serializable format, handling e.g. Numpy arrays """
    from numpy import asarray, dtype, nan, float64

    if isinstance(x, dict):
        dk = x.keys()
        if len(dk) == 2 and 'np_array' in dk:
            return asarray(fromjson(x['np_array']), dtype(x['np_dtype']))
        elif len(dk) == 1 and 'np_float64' in dk:
            return float64(x['np_float64'])
        else:
            return dict( (k, fromjson(v)) for k,v in x.iteritems() )
    elif isinstance(x, (list, tuple)):
        return type(x)( fromjson(v) for v in x )
    elif x is None:
        return nan
    else:
        return x


def upload_dir_user(dirpath, user_id = None):

    try:
        from flask.ext.login import current_user # pylint: disable=E0611,F0401

        # get current user
        if current_user.is_anonymous() == False:

            current_user_id = user_id if user_id else current_user.id

            # user_path
            user_path = os.path.join(dirpath, str(current_user_id))

            # if dir does not exist
            if not(os.path.exists(dirpath)):
                os.makedirs(dirpath)

            # if dir with user id does not exist
            if not(os.path.exists(user_path)):
                os.makedirs(user_path)

            return user_path
    except:
        return dirpath

    return dirpath