##
# @file web/dictionaries/models.py
# @brief Models for dictionary measurements

from django.db import models
from measurements.models import Measurement
import six

#the values depends on pk from petrophysics.json. The DICT_PERIOD, DICT_EPOCH, DICT_LITHOSTRATIGRAPHY, DICT_LINK primary keys are used.
stratigraphy_list = [12, 13, 14, 15]

class DictionaryMeasurement(Measurement):
    dictionary = models.ForeignKey('meanings.MeaningDictValue')
    meaning = models.ForeignKey('meanings.MeaningDict')

    def to_dict(self):
        return super(DictionaryMeasurement, self).to_dict() + [six.text_type(self.dictionary.value)]
