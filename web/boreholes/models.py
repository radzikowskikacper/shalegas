# @file web/boreholes/models.py
# @brief Models for boreholes. Contains Borehole class

from django.db import models
from django.http.response import HttpResponse
import json
import six

version = 0


def _JsonResponse(data):
    return HttpResponse(json.dumps(data), content_type='application/json')


def get(_id=None):
    '''
    The function for getting a list of all existing boreholes or one with particular id
    '''

    bholes = Borehole.objects.get(id=_id).to_dict() if _id else [
        bh.to_dict() for bh in Borehole.objects.all()]

    global version
    ret = {'boreholes_version': version, 'boreholes': bholes}

    return _JsonResponse(ret)


class Borehole(models.Model):
    name = models.CharField(max_length=64, unique=True)

    latitude = models.DecimalField(decimal_places=5, max_digits=7)
    longitude = models.DecimalField(decimal_places=5, max_digits=8)

    coordinateX = models.CharField(
        max_length=64, default='', blank=True, null=True)
    coordinateY = models.CharField(
        max_length=64, default='', blank=True, null=True)

    description = models.CharField(
        max_length=256,
        default='',
        blank=True,
        null=True)

    altitude = models.DecimalField(decimal_places=2, max_digits=6, default='0')
    bushing = models.DecimalField(decimal_places=2, max_digits=6, default='0')

    def to_dict(self):
        return {
            attr: six.text_type(
                getattr(
                    self,
                    attr,
                    '')) for attr in (
                "id",
                "name",
                "latitude",
                "longitude",
                "coordinateX",
                "coordinateY",
                "description",
                "altitude",
                "bushing")}


class BoreholesDuplicated(Exception):
    def __init__(self):
        Exception.__init__(self, 'borehole_exists')
