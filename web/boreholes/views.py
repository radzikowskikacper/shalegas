##
# @file web/boreholes/views.py
# @brief The views module for boreholes application.

from boreholes.models import BoreholesDuplicated
from django.db import transaction
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Borehole, get
import json
import logging
from . import models

logger = logging.getLogger('sweetspot.boreholes')


@ensure_csrf_cookie
def boreholes(request, borehole_id=None):
    '''
    The main boreholes service.
    Contains methods for getting all boreholes, particular borehole(using id), adding, modifying, and deleting a borehole
    '''

    if borehole_id is None:
        if request.method == 'GET':
            return get()

        elif request.method == 'POST':
            params = json.loads(request.read().decode('utf-8'))
            with transaction.atomic():
                if Borehole.objects.filter(name=params['name']).exists():
                    raise BoreholesDuplicated

                elem = {
                    'name': params['name'],
                    'latitude': params['latitude'],
                    'longitude': params['longitude']}
                elem.update(
                    {
                        key: params[key] for key in params.keys() if key in (
                            'name',
                            'bushing',
                            'altitude',
                            'latitude',
                            'longitude',
                            'coordinateX',
                            'coordinateY',
                            'description')})
                Borehole.objects.create(**elem)

                models.version += 1
                logger.info(
                    "User %s added new borehole" %
                    request.user.username)
                return get()

    else:
        if request.method == 'GET':
            return get(borehole_id)

        elif request.method == 'PUT':
            params = json.loads(request.read().decode('utf-8'))

            with transaction.atomic():
                b = Borehole.objects.get(id=borehole_id)

                if 'name' in params:
                    b.name = params['name']
                if 'latitude' in params:
                    b.latitude = params['latitude']
                if 'longitude' in params:
                    b.longitude = params['longitude']
                if 'description' in params:
                    b.description = params['description']
                if 'coordinateX' in params:
                    b.coordinateX = params['coordinateX']
                if 'coordinateY' in params:
                    b.coordinateY = params['coordinateY']
                if 'altitude' in params:
                    b.altitude = params['altitude']
                if 'bushing' in params:
                    b.bushing = params['bushing']

                b.save()

                global version
                models.version += 1
                logger.info(
                    "User %s modified borehole" %
                    request.user.username)

                return get(borehole_id)

        elif request.method == 'DELETE':
            with transaction.atomic():
                Borehole.objects.get(id=borehole_id).delete()
                models.version += 1
                logger.info("User %s deleted borehole" % request.user.username)

                return get()
