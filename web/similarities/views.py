##
# @file web/similarities/views.py
# @brief Services for calculating similarity between boreholes

from measurements.views import _JsonResponse
from similarities.calculations import compareTo


def similarities(request, borehole_id):
    if request.method == 'GET':
        ret = compareTo(
            borehole_id,
            request.GET['stratigraphy_level'],
            request.GET['epochs'],
            request.GET.getlist('filter')) if 'filter' in request.GET else compareTo(
            borehole_id,
            request.GET['stratigraphy_level'],
            request.GET.getlist('epochs'))
        return _JsonResponse(ret)
