##
# @file web/current/views.py
# @brief Current state interface, it returns the server time, logged user id and identifier of current version of application data.

import boreholes.models
from .models import time


def get(request):
    """current parameters of server"""

    global version
    versions = {'boreholes': boreholes.models.version, 'params': 1}
    ret = {'versions': versions, 'time': time({})}

    try:
        if request.user.is_authenticated():
            ret['username'] = request.user.username
            ret['uid'] = request.user.id
            #ret['name'] = request.user.first_name
            #ret['surname'] = request.user.last_name
    except AttributeError:
        pass

    return ret
