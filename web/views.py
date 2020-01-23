##
# @file web/views.py
# @brief Main interface to server

import json
import logging, traceback
import traceback

import boreholes
from boreholes.models import Borehole
import boreholes.views
import current
import current.views
from django.core.exceptions import ValidationError
from django.db import DataError
from django.http import HttpResponseServerError, HttpResponse
import django.http
from django.views.decorators.csrf import ensure_csrf_cookie
from meanings.models import *
from measurements.models import Measurement
import users.views, users
import version
import version.views
from django.contrib.auth.models import Group, User


#all modules should be imported here
logger = logging.getLogger('sweetspot.views')

@ensure_csrf_cookie
def index(request, _):
    """for test working server"""
    return django.http.HttpResponse("SweetSpot main screen" )

@ensure_csrf_cookie
def ajax(request, module, function):
    try:
        fun = getattr(getattr(globals()[str(module)], 'views'), str(function))

        data = json.dumps( fun(request) )

        return django.http.HttpResponse(data, content_type='application/json')
    except Exception as e:
        logger.error('ajax:' + str(traceback.format_exc()))
        return django.http.HttpResponseNotFound("sweetspot ajax, error: " + str(traceback.format_exc()) )
    except:
        logger.error('ajax, unknown exception')
        return django.http.HttpResponseNotFound("sweetspot ajax, system error " )

class CustomMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not('command' in view_kwargs and view_kwargs['command'] == 'login' and request.method == 'POST' or 
               'function' in view_kwargs and view_kwargs['function'] == 'get' and 'module' in view_kwargs and view_kwargs['module'] in ['current', 'version']):
            return
            if not request.user.is_authenticated():
                return HttpResponseServerError('not_logged')
            
            if request.method == 'GET':
                if not request.user.groups.filter(name='viewers').exists():
                    return HttpResponseServerError('insufficient_permissions_v')
            elif request.method in ['POST', 'PUT', 'DELETE']:
                if not('command' in view_kwargs and view_kwargs['command'] == 'logout' and request.method == 'POST'):
                    if not request.user.groups.filter(name='editors').exists():
                        return HttpResponseServerError('insufficient_permissions_e')
            
    
    def process_exception(self, request, exception):
        if isinstance(exception, KeyError) or isinstance(exception, ValueError):
            exception = 'bad_request'
        elif isinstance(exception, IndexError):
            exception = 'wrong_column_number'
        elif isinstance(exception, MeaningValue.DoesNotExist):# or isinstance(exception, MeaningDict.DoesNotExist):
            exception = 'no_meaning'
        elif isinstance(exception, MeaningDictValue.DoesNotExist):
            exception = 'no_dict_value'
        elif isinstance(exception, MeaningSection.DoesNotExist):
            exception = 'no_section'
        elif isinstance(exception, Borehole.DoesNotExist):
            exception = 'no_borehole'
        elif isinstance(exception, Measurement.DoesNotExist):
            exception = 'no_measurement'
        elif isinstance(exception, DataError):
            exception = 'field_name_too_long'
        elif isinstance(exception, ValidationError):
            exception = 'wrong_data_type'
            
        #print traceback.format_exc()
#        if exception != 'not_logged':
        logger.error(traceback.format_exc())
        return HttpResponseServerError(exception)