##
# @file web/values/models.py
# @brief Models with class describing real measurement

from django.db import models
from measurements.models import Measurement


class NoDictionaryFile(Exception):
    def __init__(self):
        Exception.__init__(self, 'no_dict_file')


class RealMeasurement(Measurement):
    value = models.FloatField()
    meaning = models.ForeignKey('meanings.MeaningValue')

    def to_dict(self):
        ret = super(RealMeasurement, self).to_dict()
        ret.insert(1, self.value)
        return ret
