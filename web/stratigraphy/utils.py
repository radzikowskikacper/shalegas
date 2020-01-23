# @file web/stratigraphy/utils.py
# @brief Utility functions for stratigraphy.views services

from boreholes.models import _JsonResponse
from dictionaries.models import DictionaryMeasurement
from measurements.utils import prepareFilter


def getStratigraphy(**kwargs):
    params, _, _, _ = prepareFilter(**kwargs)
    curthill, curceil = None, None
    ret = list()

    data = list(DictionaryMeasurement.objects.filter(
        **params).order_by('depth_from', 'depth_to', 'meaning'))
    for d in data:
        if d.depth_from != curthill or d.depth_to != curceil:
            curthill, curceil = d.depth_from, d.depth_to
            ret.append({'thill': d.depth_from, 'ceil': d.depth_to})
        ret[-1][d.meaning_id] = d.dictionary.value

    return _JsonResponse(ret)
